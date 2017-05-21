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
    # if there are files in the resource validate those files. If validation fails
    # all or some of the files get deleted.
    # if validation is successful extract metadata

    resource = kwargs['resource']
    res_file = None
    base_err_msg = "Files failed validation. Files not uploaded are: {}"
    files_failed_validation = []
    if resource.files.all().count() == 0:
        # resource was created without any uploaded files - no file validation needed
        return
    elif resource.files.all().count() == 1:
        # this file has to be a zip file
        res_file = resource.files.all().first()
        if res_file.extension != '.zip':
            files_failed_validation.append(res_file.file_name)
            res_file.delete()
            err_msg = base_err_msg.format(", ".join(files_failed_validation))
            raise ValidationError(err_msg)
    elif not resource.has_required_content_files():
        for f in resource.files.all():
            files_failed_validation.append(f.file_name)
            f.delete()
        err_msg = base_err_msg.format(", ".join(files_failed_validation))
        raise ValidationError(err_msg)
    else:
        # validate files by extension
        for f in resource.files.all():
            if f.extension.lower() not in \
                    geofeature.GeoFeatureLogicalFile.get_allowed_storage_file_types():
                files_failed_validation.append(f.file_name)
                f.delete()
        # check that there are no files with duplicate extension, otherwise delete all files
        file_extensions = set([f.extension.lower() for f in resource.files.all()])
        if len(file_extensions) != resource.files.count():
            for f in resource.files.all():
                if f.file_name not in files_failed_validation:
                    files_failed_validation.append(f.file_name)
                f.delete()
            err_msg = base_err_msg.format(", ".join(files_failed_validation))
            raise ValidationError(err_msg)
        # check that there are no files with duplicate name (without extension),
        # otherwise delete all files
        file_names = set([f.file_name[:-4] for f in resource.files.all() if
                          f.extension.lower() != '.xml'])
        if len(file_names) > 1:
            for f in resource.files.all():
                if f.file_name not in files_failed_validation:
                    files_failed_validation.append(f.file_name)
                f.delete()
            err_msg = base_err_msg.format(", ".join(files_failed_validation))
            raise ValidationError(err_msg)
        # validate .shp.xml file
        xml_files = [f for f in resource.files.all() if f.extension.lower() == '.xml']
        if xml_files:
            xml_file = xml_files[0]
            if not xml_file.file_name.lower().endswith('.shp.xml') or xml_file.file_name[:-8] not \
                    in file_names:
                if xml_file.file_name not in files_failed_validation:
                    files_failed_validation.append(xml_file.file_name)
                xml_file.delete()

    # process the uploaded files
    if res_file is None:
        # find the shp file - at this point there must be a .shp file
        for f in resource.files.all():
            if f.extension.lower() == '.shp':
                res_file = f
                break
    try:
        _process_uploaded_file(resource, res_file, base_err_msg)
    except Exception as ex:
        raise ValidationError(ex.message)

    if files_failed_validation:
        # some files got deleted
        err_msg = base_err_msg.format(", ".join(files_failed_validation))
        raise ValidationError(err_msg)


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
    if del_res_file.extension.lower() in ('.shp', '.shx', '.dbf'):
        for f in resource.files.all():
            if f.file_name != del_res_file.file_name:
                f.delete()
        # delete all resource specific metadata associated with the resource
        resource.metadata.reset()
    elif del_res_file.extension.lower() == ".prj":
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
    base_err_msg = "Files failed validation. Files not uploaded are: {}."
    resource = kwargs['resource']
    added_res_files = kwargs['res_files']
    validate_files_dict = kwargs['validate_files']
    shp_res_file = None
    zip_res_file = None
    zip_file_added = False
    shp_file_added = False
    prj_file_added = False
    xml_file_added = False
    files_failed_validation = []
    files_existed_before = len(added_res_files) < resource.files.count()
    if resource.files.all().count() == 1:
        # this file has to be a zip file
        res_file = resource.files.all().first()
        if res_file.extension.lower() != '.zip':
            files_failed_validation.append(res_file.file_name)
            res_file.delete()
            validate_files_dict['are_files_valid'] = False
            err_msg = base_err_msg.format(", ".join(files_failed_validation))
            validate_files_dict['message'] = err_msg
            return
        zip_file_added = True
        zip_res_file = res_file

    # check if we have the required content files - otherwise delete all files
    elif not resource.has_required_content_files():
        for f in resource.files.all():
            files_failed_validation.append(f.file_name)
            f.delete()
        resource.metadata.reset()
        validate_files_dict['are_files_valid'] = False
        err_msg = base_err_msg.format(", ".join(files_failed_validation))
        validate_files_dict['message'] = err_msg
        return
    else:
        for f in added_res_files:
            # if there are already other files, a zip file can't be added
            if f.extension.lower() == '.zip':
                files_failed_validation.append(f.file_name)
                f.delete()
                added_res_files.remove(f)

    if not zip_file_added:
        for f in added_res_files:
            # validate files by extension
            if f.extension.lower() not in \
                    geofeature.GeoFeatureLogicalFile.get_allowed_storage_file_types():
                files_failed_validation.append(f.file_name)
                f.delete()
                added_res_files.remove(f)
            # check that we din't add a file with existing extension
            files_with_same_extension = [fl for fl in resource.files.exclude(id=f.id) if
                                         fl.extension.lower() == f.extension.lower()]
            if len(files_with_same_extension) > 0:
                files_failed_validation.append(f.file_name)
                f.delete()
                added_res_files.remove(f)
            elif f.extension.lower() == '.xml' and not f.file_name.lower().endswith('.shp.xml'):
                files_failed_validation.append(f.file_name)
                f.delete()
                added_res_files.remove(f)
        if not added_res_files:
            validate_files_dict['are_files_valid'] = False
            err_msg = base_err_msg.format(", ".join(files_failed_validation))
            validate_files_dict['message'] = err_msg
            return

        # test file names (without extension) are same for the newly added files
        if len(added_res_files) > 1:
            file_names = set([f.file_name[:-4] for f in added_res_files if
                              f.extension.lower() != '.xml'])
            # if one of the added files has a different name then we going to delete all added
            # files
            if len(file_names) > 1:
                for f in added_res_files:
                    files_failed_validation.append(f.file_name)
                    f.delete()
                validate_files_dict['are_files_valid'] = False
                err_msg = base_err_msg.format(", ".join(files_failed_validation))
                validate_files_dict['message'] = err_msg
                return
            if files_existed_before:
                # added file name must match with existing file name
                added_file_ids = [f.id for f in added_res_files]
                file_name_to_match = [f.file_name for f in resource.files.all() if f.id not
                                      in added_file_ids][0]
                added_file_non_xml = [f for f in added_res_files if
                                      f.extension.lower() != '.xml'][0]
                match_file_offset = -4
                if file_name_to_match.lower().endswith('.shp.xml'):
                    match_file_offset = -8

                if added_file_non_xml.file_name[:-4] != file_name_to_match[:match_file_offset]:
                    files_failed_validation.append(added_file_non_xml.file_name)
                    added_file_non_xml.delete()
                    added_res_files.remove(added_file_non_xml)

                added_files_xml = [f for f in added_res_files if f.extension.lower() == '.xml']
                if added_files_xml:
                    added_xml_file = added_files_xml[0]
                    if added_xml_file.file_name[:-8] != file_name_to_match[:match_file_offset]:
                        files_failed_validation.append(added_xml_file.file_name)
                        added_xml_file.delete()
                        added_res_files.remove(added_xml_file)

        elif resource.files.count() > 1:
            # case of only one non-zip file got added - this file must be one of the optional files
            # validate the name of the added file
            added_res_file = added_res_files[0]
            file_name_to_match = [f.file_name for f in resource.files.all() if
                                  f.extension.lower() == '.shp'][0]
            file_offset = -4
            if added_res_file.extension.lower() == '.xml':
                # compare the xml file without '.shp.xml' part (-8)
                file_offset = -8
            if added_res_file.file_name[:file_offset] != file_name_to_match[:-4]:
                files_failed_validation.append(added_res_file.file_name)
                added_res_file.delete()
                added_res_files.remove(added_res_file)
                validate_files_dict['are_files_valid'] = False
                err_msg = base_err_msg.format(", ".join(files_failed_validation))
                validate_files_dict['message'] = err_msg
                return

        # check if a shp file got added - in that case resource specific metadata needs
        # to be created
        shp_res_file = None
        for f in added_res_files:
            if f.extension.lower() == '.shp':
                shp_res_file = f
                shp_file_added = True
                break
        if not shp_file_added:
            # metadata needs to be re-extracted and updated only if a prj or a xml file has
            # been added
            file_extensions = [f.extension.lower() for f in added_res_files]
            prj_file_added = '.prj' in file_extensions
            shp_file_added = '.shp' in file_extensions
            xml_file_added = '.xml' in file_extensions

            for f in resource.files.all():
                if f.extension.lower() == '.shp':
                    shp_res_file = f
                    break

    if any([zip_file_added, shp_file_added, prj_file_added, xml_file_added]):
        if zip_file_added:
            res_file = zip_res_file
        else:
            res_file = shp_res_file
        try:
            _process_uploaded_file(resource, res_file, base_err_msg)
        except Exception as ex:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = ex.message

    if files_failed_validation:
        # some of the uploaded files did not pass validation
        validate_files_dict['are_files_valid'] = False
        err_msg = base_err_msg.format(", ".join(files_failed_validation))
        validate_files_dict['message'] = err_msg


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
    files_failed_validation = []
    try:
        # validate files and extract metadata
        meta_dict, shape_files, shp_res_files = geofeature.extract_metadata_and_files(
            resource, res_file, file_type=False)
    except Exception:
        # need to delete all resource files as these files failed validation
        for f in resource.files.all():
            files_failed_validation.append(f.file_name)
            f.delete()

        err_msg = err_msg.format(", ".join(files_failed_validation))
        raise ValidationError(err_msg)
    # upload generated files in case of zip file
    if res_file.extension.lower() == '.zip':
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
        if f.lower().endswith('.shp.xml'):
            xml_file = f
            break
    geofeature.add_metadata(resource, meta_dict, xml_file)
