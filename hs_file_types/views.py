# coding=utf-8
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import Error
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context

from rest_framework import status

from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
from .utils import set_file_to_geo_raster_file_type
from .models import GeoRasterLogicalFile, GenericLogicalFile


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
    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching logical file type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

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
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'message': err_msg}
        # need to return http status 200 to show form errors
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def add_metadata_element(request, hs_file_type, file_type_id, element_name, **kwargs):
    err_msg = "Failed to create metadata element '{}'. {}."
    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching logical file type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    resource = logical_file.resource
    res, _, _ = authorize(request, resource.short_id,
                          needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_add_success = False
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            element = logical_file.metadata.create_element(element_name, **element_data_dict)
            is_add_success = True
        except ValidationError as ex:
            err_msg = err_msg.format(element_name, ex.message)
        except Error as ex:
            err_msg = err_msg.format(element_name, ex.message)
    else:
        err_msg = err_msg.format(element_name, validation_response['errors'])

    if is_add_success:
        form_action = "/hsapi/_internal/{0}/{1}/{2}/{3}/update-file-metadata/"
        form_action = form_action.format(logical_file.type_name(), logical_file.id, element_name,
                                         element.id)

        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'element_name': element_name, 'form_action': form_action,
                              'element_id': element.id, 'metadata_status': "Update was successful"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'message': err_msg}
        # need to return http status 200 to show form errors
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_key_value_metadata(request, hs_file_type, file_type_id, **kwargs):
    """add/update key/value extended metadata for a given logical file
    key/value data is expected as part of the request.POST data
    If the key already exists, the value then gets updated, otherwise, the key/value is added
    to the hstore dict type field
    """
    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    key = request.POST['key']
    value = request.POST['value']
    logical_file.metadata.extra_metadata[key] = value
    logical_file.metadata.save()
    extra_metadata_div = super(logical_file.metadata.__class__,
                               logical_file.metadata).get_html_forms()
    context = Context({})
    template = Template(extra_metadata_div.render())
    rendered_html = template.render(context)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'extra_metadata': rendered_html,
                          'message': "Update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def get_metadata(request, hs_file_type, file_type_id, metadata_mode):
    """
    Gets metadata html for the logical file type
    :param request:
    :param hs_file_type: HydroShare supported logical file type class name
    :param file_type_id: id of the logical file object for which metadata in html format is needed
    :param metadata_mode: a value of either edit or view. In edit mode metadata html form elements
                          are returned. In view mode normal html for display of metadata is returned
    :return: json data containing html string
    """
    if metadata_mode != "edit" and metadata_mode != 'view':
        err_msg = "Invalid metadata type request."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()

    if logical_file is None:
        err_msg = "No matching file type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    if metadata_mode == 'view':
        metadata = logical_file.metadata.get_html()
    else:
        metadata = logical_file.metadata.get_html_forms()

    ajax_response_data = {'status': 'success', 'metadata': metadata}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


def _get_logical_file(hs_file_type, file_type_id):
    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching logical file type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return None, JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    return logical_file, None
