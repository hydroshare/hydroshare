import os
import logging
import shutil

from django.core.files.uploadedfile import UploadedFile
from django.dispatch import receiver

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import ResourceFile, \
    get_resource_file_name, delete_resource_file_only, delete_format_metadata_after_delete_file
from hs_core.signals import pre_delete_file_from_resource, pre_metadata_element_create, \
    pre_metadata_element_update, post_create_resource, post_add_files_to_resource

from forms import CellInfoValidationForm, BandInfoValidationForm, OriginalCoverageSpatialForm
from models import RasterResource
from hs_file_types.models import raster


@receiver(post_create_resource, sender=RasterResource)
def raster_post_create_resource_trigger(sender, **kwargs):
    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    _process_uploaded_file(resource, validate_files_dict)
    # since we are extracting metadata after resource creation
    # metadata xml files need to be regenerated - so need to set the
    # dirty bag flags
    if resource.files.all().count() > 0:
        utils.set_dirty_bag_flag(resource)


@receiver(post_add_files_to_resource, sender=RasterResource)
def raster_post_add_files_to_resource_trigger(sender, **kwargs):
    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    _process_uploaded_file(resource, validate_files_dict)


@receiver(pre_delete_file_from_resource, sender=RasterResource)
def raster_pre_delete_file_from_resource_trigger(sender, **kwargs):
    res = kwargs['resource']
    del_file = kwargs['file']
    del_res_fname = get_resource_file_name(del_file)
    # delete core metadata coverage now that the only file is deleted
    res.metadata.coverages.all().delete()

    # delete all other resource specific metadata
    res.metadata.originalCoverage.delete()
    res.metadata.cellInformation.delete()
    res.metadata.bandInformations.all().delete()

    # delete all the files that is not the user selected file
    for f in ResourceFile.objects.filter(object_id=res.id):
        fname = get_resource_file_name(f)
        if fname != del_res_fname:
            delete_resource_file_only(res, f)

    # delete the format of the files that is not the user selected delete file
    del_file_format = utils.get_file_mime_type(del_res_fname)
    for format_element in res.metadata.formats.all():
        if format_element.value != del_file_format:
            res.metadata.delete_element(format_element.term, format_element.id)


@receiver(pre_metadata_element_create, sender=RasterResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        element_form = BandInfoValidationForm(request.POST)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)
    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


@receiver(pre_metadata_element_update, sender=RasterResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    """
    Since each of the Raster metadata element is required no need to listen to any delete signal
    The Raster landing page should not have delete UI functionality for the resource
    specific metadata elements
    """
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    if element_name == "cellinformation":
        element_form = CellInfoValidationForm(request.POST)
    elif element_name == 'bandinformation':
        form_data = {}
        for field_name in BandInfoValidationForm().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]
        element_form = BandInfoValidationForm(form_data)
    elif element_name == 'originalcoverage':
        element_form = OriginalCoverageSpatialForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


def _process_uploaded_file(resource, validate_files_dict):
    log = logging.getLogger()

    # find a tif file or a zip file
    res_file = None
    for r_file in resource.files.all():
        if r_file.extension.lower() in ('.tif', '.tiff', '.zip'):
            res_file = r_file
            break

    if res_file:
        # get the file from irods to temp dir
        temp_file = utils.get_file_from_irods(res_file)
        # validate the file
        validation_results = raster.raster_file_validation(raster_file=temp_file,
                                                           resource=resource)
        if not validation_results['error_info']:
            log.info("Geo raster file validation successful.")
            # extract metadata
            temp_dir = os.path.dirname(temp_file)
            temp_vrt_file_path = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if
                                  '.vrt' == os.path.splitext(f)[1]].pop()
            metadata = raster.extract_metadata(temp_vrt_file_path)
            # delete the original resource file if it is a zip file
            if res_file.extension.lower() == '.zip':
                file_name = delete_resource_file_only(resource, res_file)
                delete_format_metadata_after_delete_file(resource, file_name)
            # add all extracted files (tif and vrt)
            for f in validation_results['new_resource_files_to_add']:
                uploaded_file = UploadedFile(file=open(f, 'rb'),
                                             name=os.path.basename(f))
                utils.add_file_to_resource(resource, uploaded_file)

            # use the extracted metadata to populate resource metadata
            for element in metadata:
                # here k is the name of the element
                # v is a dict of all element attributes/field names and field values
                k, v = element.items()[0]
                resource.metadata.create_element(k, **v)
            log_msg = "Geo raster resource (ID:{}) - extracted metadata was saved to DB"
            log_msg = log_msg.format(resource.short_id)
            log.info(log_msg)
        else:
            # delete all the files in the resource
            for res_file in resource.files.all():
                delete_resource_file_only(resource, res_file)
            validate_files_dict['are_files_valid'] = False
            err_msg = "Uploaded file was not added to the resource. "
            err_msg += ", ".join(msg for msg in validation_results['error_info'])
            validate_files_dict['message'] = err_msg
            log_msg = "File validation failed for raster resource (ID:{})."
            log_msg = log_msg.format(resource.short_id)
            log.error(log_msg)

        # cleanup the temp file directory
        if os.path.exists(temp_file):
            shutil.rmtree(os.path.dirname(temp_file))
