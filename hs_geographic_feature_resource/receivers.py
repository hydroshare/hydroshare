import os
import logging

from django.db import transaction
from django.dispatch import receiver
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError

from hs_core.hydroshare import utils
from hs_core.signals import post_create_resource, pre_metadata_element_create,\
                            pre_metadata_element_update, pre_delete_file_from_resource,\
                            post_add_files_to_resource

from hs_geographic_feature_resource.forms import OriginalCoverageValidationForm,\
                                                 GeometryInformationValidationForm,\
                                                 FieldInformationValidationForm
from hs_geographic_feature_resource.models import GeographicFeatureResource

from hs_file_types.models import geofeature

logger = logging.getLogger(__name__)


@receiver(post_create_resource, sender=GeographicFeatureResource)
def post_create_resource(sender, **kwargs):
    # here we need to check if the resource has any files
    # and make sure the resource then has the 3 required files
    # if any of the required shape file is missing then we will delete all files

    resource = kwargs['resource']
    res_file = None
    err_msg = "Required shape files are missing. Files were not uploaded."
    if resource.files.all().count() == 0:
        return
    elif resource.files.all().count() == 1:
        # this file has to be a zip file
        res_file = resource.files.all().first()
        if res_file.extension != '.zip':
            res_file.delete()
            raise ValidationError(err_msg)
    elif resource.files.all().count() < 3:
        # there needs to be 3 file at least
        for f in resource.files.all():
            f.delete()
        raise ValidationError(err_msg)

    # process the uploaded files
    if res_file is None:
        # find the shp file
        for f in resource.files.all():
            if f.extension == '.shp':
                res_file = f
                break
        # if shp file doesn't exist then delete all uploaded files
        if res_file is None:
            for f in resource.files.all():
                f.delete()
            raise ValidationError(err_msg)

    try:
        _process_uploaded_file(resource, res_file, err_msg)
    except Exception as ex:
        raise ValidationError(ex.message)


# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_create, sender=GeographicFeatureResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return validate_form(request, element_name)


# This handler is executed only when a metadata element is updated as part of editing a resource
@receiver(pre_metadata_element_update, sender=GeographicFeatureResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return validate_form(request, element_name)


@receiver(pre_delete_file_from_resource, sender=GeographicFeatureResource)
def pre_delete_file_from_resource(sender, **kwargs):
    resource = kwargs['resource']
    del_res_file = kwargs['file']

    # check if one of the required files is getting deleted
    # if so then delete all files except the del_res_file
    if del_res_file.extension in ('.shp', '.shx', '.dbf'):
        for f in resource.files.all():
            if f.file_name != del_res_file.file_name:
                f.delete()
        # delete all resource specific metadata associated with the resource
        resource.metadata.reset()
    elif del_res_file.extension == ".prj":
        original_coverage = resource.metadata.originalcoverage
        resource.metadata.update_element('originalcoverage',
                                         element_id=original_coverage.id,
                                         projection_string=geofeature.UNKNOWN_STR,
                                         projection_name=geofeature.UNKNOWN_STR,
                                         datum=geofeature.UNKNOWN_STR,
                                         unit=geofeature.UNKNOWN_STR)
        resource.metadata.coverages.all().delete()


@receiver(post_add_files_to_resource, sender=GeographicFeatureResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    err_msg = "Required shape files are missing. Files were not uploaded."
    resource = kwargs['resource']
    added_res_files = kwargs['res_files']
    validate_files_dict = kwargs['validate_files']
    shp_res_file = None
    zip_res_file = None
    zip_file_added = False
    shp_file_added = False
    prj_file_added = False
    if resource.files.all().count() == 1:
        # this file has to be a zip file
        res_file = resource.files.all().first()
        if res_file.extension != '.zip':
            res_file.delete()
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = err_msg
            return
        zip_file_added = True
        zip_res_file = res_file

    # check if we have the required content files - otherwise delete all files
    elif not resource.has_required_content_files():
        for f in resource.files.all():
            f.delete()
        resource.metadata.reset()
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = err_msg
        return
    else:
        for f in added_res_files:
            # if there are already other files, a zip file can't be added
            if f.extension == '.zip':
                # delete all files that just get added
                for fl in added_res_files:
                    fl.delete()
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = err_msg
                return

    # validate files by extension
    if not zip_file_added:
        for f in added_res_files:
            if f.extension not in geofeature.GeoFeatureLogicalFile.get_allowed_storage_file_types():
                f.delete()
                added_res_files.remove(f)
            # check that we din't add a file with existing extension
            files_with_same_extension = [fl for fl in resource.files.exclude(id=f.id) if
                                         fl.extension == f.extension]
            if len(files_with_same_extension) > 0:
                f.delete()
                added_res_files.remove(f)

        if not added_res_files:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = err_msg
            return

        # test file names (without extension) are same for the newly added files
        file_names = set([f.file_name[:-4] for f in added_res_files])
        if len(file_names) > 1:
            for f in added_res_files:
                f.delete()
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = err_msg
            return

        # check if a shp file got added - in that case resource specific metadata needs
        # to be created
        shp_res_file = None
        for f in added_res_files:
            if f.extension == '.shp':
                shp_res_file = f
                shp_file_added = True
                break
        if not shp_file_added:
            # metadata needs to be re-extracted and updated only if a prj file has been added
            for f in added_res_files:
                if f.extension == '.prj':
                    prj_file_added = True
                    break
            for f in resource.files.all():
                if f.extension == '.shp':
                    shp_res_file = f
                    break

    if zip_file_added or shp_file_added or prj_file_added:
        if zip_file_added:
            res_file = zip_res_file
        else:
            res_file = shp_res_file
        try:
            _process_uploaded_file(resource, res_file, err_msg)
        except Exception as ex:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = ex.message


def validate_form(request, element_name):
    element_form = None
    if element_name == 'originalcoverage':
        element_form = OriginalCoverageValidationForm(data=request.POST)
    elif element_name == 'geometryinformation':
        element_form = GeometryInformationValidationForm(data=request.POST)
    elif element_name == 'fieldinformation':
        element_form = FieldInformationValidationForm(data=request.POST)

    if element_form is not None and element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


def _process_uploaded_file(resource, res_file, err_msg):
    try:
        # validate files and extract metadata
        meta_dict, shape_files, shp_res_files = geofeature.extract_metadata_and_files(
            resource, res_file, file_type=False)
    except Exception:
        # need to delete all resource files as these files failed validation
        for f in resource.files.all():
            f.delete()
        raise ValidationError(err_msg)
    # upload generated files in case of zip file
    if res_file.extension == '.zip':
        with transaction.atomic():
            # delete the zip file
            res_file.delete()
            # uploaded the extracted files
            for fl in shape_files:
                uploaded_file = UploadedFile(file=open(fl, 'rb'),
                                             name=os.path.basename(fl))
                utils.add_file_to_resource(resource, uploaded_file)
    # add extracted metadata to the resource
    xml_file = ''
    for f in shape_files:
        if f.endswith('.xml'):
            xml_file = f
            break
    geofeature.add_metadata(resource, meta_dict, xml_file)
