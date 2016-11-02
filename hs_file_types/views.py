# coding=utf-8
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import Error
from rest_framework import status

from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
from .utils import set_file_to_geo_raster_file_type
from .models import GeoRasterLogicalFile

@login_required
def set_file_type(request, resource_id, file_id, hs_file_type,  **kwargs):
    """This view function must be called using ajax call"""
    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    if res.resource_type != "CompositeResource":
        err_msg = "File type can be set only for files in composite resource."
        return JsonResponse({'message': err_msg}, status=status.HTTP_400_BAD_REQUEST)

    if hs_file_type != "GeoRaster":
        err_msg = "Currently a file can be set to Geo Raster file type."
        return JsonResponse({'message': err_msg}, status=status.HTTP_400_BAD_REQUEST)

    try:
        set_file_to_geo_raster_file_type(resource=res, file_id=file_id, user=request.user)
        msg = "File was successfully set to Geo Raster file type. " \
              "Raster metadata extraction was successful."
        return JsonResponse({'message': msg}, status=status.HTTP_200_OK)

    except ValidationError as ex:
        return JsonResponse({'message': ex.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@login_required
def delete_file_type(request, resource_id, hs_file_type, file_type_id, **kwargs):
    """deletes an instance of a specific file type and all its associated resource files"""

    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "CompositeResource":
        err_msg = "File type can be deleted only in composite resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if hs_file_type != "GeoRaster":
        err_msg = "Currently only an instance of Geo Raster file type can be deleted."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    logical_file_to_delete = GeoRasterLogicalFile.objects.filter(id=file_type_id).first()
    if logical_file_to_delete is None:
        err_msg = "No matching Geo Raster file type was found."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if logical_file_to_delete.resource.short_id != res.short_id:
        err_msg = "Geo Raster file type doesn't belong to the specified resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    logical_file_to_delete.logical_delete(request.user)
    msg = "Geo Raster file type was deleted."
    messages.success(request, msg)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def update_metadata_element(request, hs_file_type, file_type_id, element_name,
                            element_id, **kwargs):
    err_msg = "Failed to update metadata element '{}'. {}."
    if hs_file_type != "GeoRaster":
        err_msg = "Currently only metadata can be updated for Geo Raster file type."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data)

    logical_file = GeoRasterLogicalFile.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching Geo Raster file type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data)

    resource = logical_file.resource
    res, _, _ = authorize(request, resource.short_id,
                          needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_update_success = False
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            logical_file.metadata.update_element(element_name, element_id, **element_data_dict)
            is_update_success = True
        except ValidationError as ex:
            err_msg = err_msg.format(element_name, ex.message)
        except Error as ex:
            err_msg = err_msg.format(element_name, ex.message)
    else:
        err_msg = err_msg.format(element_name, validation_response['errors'])

    if is_update_success:
        ajax_response_data = {'status': 'success', 'element_name': element_name,
                              'metadata_status': "Update was successful"}
    else:
        ajax_response_data = {'status': 'error', 'message': err_msg}

    return JsonResponse(ajax_response_data)