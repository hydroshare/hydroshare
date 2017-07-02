import os
import json

from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import Error
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context

from rest_framework import status
from rest_framework.decorators import api_view

from hs_core.hydroshare import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    ResourceFile, utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize, get_coverage_data_dict
from hs_core.hydroshare.utils import resource_modified

from .models import GeoRasterLogicalFile, NetCDFLogicalFile, GeoFeatureLogicalFile


@login_required
def set_file_type(request, resource_id, file_id, hs_file_type,  **kwargs):
    """This view function must be called using ajax call.
    Note: Response status code is always 200 (OK). Client needs check the
    the response 'status' key for success or failure.
    """
    res, authorized, _ = authorize(request, resource_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                   raises_exception=False)
    file_type_map = {"GeoRaster": GeoRasterLogicalFile, "NetCDF": NetCDFLogicalFile,
                     'GeoFeature': GeoFeatureLogicalFile}
    response_data = {'status': 'error'}
    if not authorized:
        err_msg = "Permission denied"
        response_data['message'] = err_msg
        response_data['status_code'] = status.HTTP_401_UNAUTHORIZED
        return JsonResponse(response_data, status=status.HTTP_200_OK)

    if res.resource_type != "CompositeResource":
        err_msg = "File type can be set only for files in composite resource."
        response_data['message'] = err_msg
        response_data['status_code'] = status.HTTP_400_BAD_REQUEST
        return JsonResponse(response_data, status=status.HTTP_200_OK)

    if hs_file_type not in file_type_map:
        err_msg = "Unsupported file type."
        response_data['message'] = err_msg
        response_data['status_code'] = status.HTTP_400_BAD_REQUEST
        return JsonResponse(response_data, status=status.HTTP_200_OK)

    try:
        logical_file_type_class = file_type_map[hs_file_type]
        logical_file_type_class.set_file_type(resource=res, file_id=file_id, user=request.user)
        resource_modified(res, request.user, overwrite_bag=False)
        msg = "File was successfully set to selected file type. " \
              "Metadata extraction was successful."
        response_data['message'] = msg
        response_data['status'] = 'success'
        spatial_coverage_dict = get_coverage_data_dict(res)
        response_data['spatial_coverage'] = spatial_coverage_dict
        response_data['status_code'] = status.HTTP_200_OK
        return JsonResponse(response_data, status=status.HTTP_200_OK)

    except ValidationError as ex:
        response_data['message'] = ex.message
        response_data['status_code'] = status.HTTP_400_BAD_REQUEST
        return JsonResponse(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def set_file_type_public(request, resource_id, file_path, hs_file_type):
    """
    Set file type as specified by *hs_file_type* using the file given by *file_path*
    :param request: an instance of HttpRequest object
    :param resource_id: id of the resource in which this file type needs to be set
    :param file_path: relative file path of the file which needs to be set to the specified file
    type
    :param hs_file_type: type of file to be set (e.g NetCDF, GeoRaster, GeoFeature etc)
    :return:
    """
    # get id of the file from the file_path to map to the internal api call
    file_rel_path = str(file_path).strip()
    if not file_rel_path:
        return JsonResponse('file_path cannot be empty',
                            status=status.HTTP_400_BAD_REQUEST)

    # security checks deny illicit requests
    # if not file_rel_path.startswith('data/contents/'):
    #     return JsonResponse('file_path must start with data/contents/',
    #                         status=status.HTTP_400_BAD_REQUEST)
    if file_rel_path.find('/../') >= 0 or file_rel_path.endswith('/..'):
        return JsonResponse('file_path must not contain /../',
                            status=status.HTTP_400_BAD_REQUEST)

    file_name = os.path.basename(file_rel_path)
    folder = os.path.dirname(file_rel_path)
    if folder == '':
        folder = None
    resource = utils.get_resource_by_shortkey(resource_id)
    try:
        res_file = ResourceFile.get(resource, file_name, folder)
    except ObjectDoesNotExist:
        return JsonResponse('no file was found for the given file_path',
                            status=status.HTTP_400_BAD_REQUEST)

    # call the internal api for setting the file type
    json_response = set_file_type(request=request, resource_id=resource_id, file_id=res_file.id,
                                  hs_file_type=hs_file_type)
    response_dict = json.loads(json_response)
    return JsonResponse(response_dict['message'], status=response_dict['status_code'])


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
    resource_modified(res, request.user, overwrite_bag=False)
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

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)

    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': element_name, 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_update_success = False
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            logical_file.metadata.update_element(element_name, element_id, **element_data_dict)
            resource_modified(resource, request.user, overwrite_bag=False)
            is_update_success = True
        except ValidationError as ex:
            err_msg = err_msg.format(element_name, ex.message)
        except Error as ex:
            err_msg = err_msg.format(element_name, ex.message)
    else:
        err_msg = err_msg.format(element_name, validation_response['errors'])

    if is_update_success:
        if resource.can_be_public_or_discoverable:
            metadata_status = METADATA_STATUS_SUFFICIENT
        else:
            metadata_status = METADATA_STATUS_INSUFFICIENT

        ajax_response_data = {'status': 'success', 'element_name': element_name,
                              'metadata_status': metadata_status,
                              'logical_file_type': logical_file.type_name()
                              }

        if element_name.lower() == 'coverage':
            spatial_coverage_dict = get_coverage_data_dict(resource)
            temporal_coverage_dict = get_coverage_data_dict(resource, coverage_type='temporal')
            ajax_response_data['spatial_coverage'] = spatial_coverage_dict
            ajax_response_data['temporal_coverage'] = temporal_coverage_dict

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

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)

    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': element_name, 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_add_success = False
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            element = logical_file.metadata.create_element(element_name, **element_data_dict)
            resource_modified(logical_file.resource, request.user, overwrite_bag=False)
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

        if resource.can_be_public_or_discoverable:
            metadata_status = METADATA_STATUS_SUFFICIENT
        else:
            metadata_status = METADATA_STATUS_INSUFFICIENT

        ajax_response_data = {'status': 'success',
                              'logical_file_type': logical_file.type_name(),
                              'element_name': element_name, 'form_action': form_action,
                              'element_id': element.id,
                              'metadata_status': metadata_status}

        if element_name.lower() == 'coverage':
            spatial_coverage_dict = get_coverage_data_dict(resource)
            temporal_coverage_dict = get_coverage_data_dict(resource, coverage_type='temporal')
            ajax_response_data['spatial_coverage'] = spatial_coverage_dict
            ajax_response_data['temporal_coverage'] = temporal_coverage_dict

        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'message': err_msg}
        # need to return http status 200 to show form errors
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_key_value_metadata(request, hs_file_type, file_type_id, **kwargs):
    """add/update key/value extended metadata for a given logical file
    key/value data is expected as part of the request.POST data for adding
    key/value/key_original is expected as part of the request.POST data for updating
    If the key already exists, the value then gets updated, otherwise, the key/value is added
    to the hstore dict type field
    """
    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)

    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'key_value', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    def validate_key():
        if key in logical_file.metadata.extra_metadata.keys():
            ajax_response_data = {'status': 'error',
                                  'logical_file_type': logical_file.type_name(),
                                  'message': "Update failed. Key already exists."}
            return False, JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
        return True, None

    key_original = request.POST.get('key_original', None)
    key = request.POST['key']
    value = request.POST['value']
    if key_original is not None:
        # user trying to update an existing pair of key/value
        if key != key_original:
            # user is updating the key
            is_valid, json_response = validate_key()
            if not is_valid:
                return json_response
            else:
                if key_original in logical_file.metadata.extra_metadata.keys():
                    del logical_file.metadata.extra_metadata[key_original]
    else:
        # user trying to add a new pair of key/value
        is_valid, json_response = validate_key()
        if not is_valid:
            return json_response

    logical_file.metadata.extra_metadata[key] = value
    logical_file.metadata.is_dirty = True
    logical_file.metadata.save()
    resource_modified(resource, request.user, overwrite_bag=False)
    extra_metadata_div = super(logical_file.metadata.__class__,
                               logical_file.metadata).get_extra_metadata_html_form()
    context = Context({})
    template = Template(extra_metadata_div.render())
    rendered_html = template.render(context)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'extra_metadata': rendered_html,
                          'message': "Update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def delete_key_value_metadata(request, hs_file_type, file_type_id, **kwargs):
    """deletes one pair of key/value extended metadata for a given logical file
    key data is expected as part of the request.POST data
    If key is found the matching key/value pair is deleted from the hstore dict type field
    """
    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'key_value', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    key = request.POST['key']
    if key in logical_file.metadata.extra_metadata.keys():
        del logical_file.metadata.extra_metadata[key]
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)

    extra_metadata_div = super(logical_file.metadata.__class__,
                               logical_file.metadata).get_extra_metadata_html_form()
    context = Context({})
    template = Template(extra_metadata_div.render())
    rendered_html = template.render(context)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'extra_metadata': rendered_html,
                          'message': "Delete was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def add_keyword_metadata(request, hs_file_type, file_type_id, **kwargs):
    """adds one or more keywords for a given logical file
    data for keywords is expected as part of the request.POST
    multiple keywords are part of the post data in a comma separated format
    If any of the keywords to be added already exists (case insensitive check) then none of
    the posted keywords is added
    NOTE: This view function must be called via ajax call
    """

    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)

    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    keywords = request.POST['keywords']
    keywords = keywords.split(",")
    existing_keywords = [kw.lower() for kw in logical_file.metadata.keywords]
    if not any(kw.lower() in keywords for kw in existing_keywords):
        logical_file.metadata.keywords += keywords
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()
        # add keywords to resource
        resource_keywords = [subject.value.lower() for subject in resource.metadata.subjects.all()]
        for kw in keywords:
            if kw.lower() not in resource_keywords:
                resource.metadata.create_element('subject', value=kw)
        resource_modified(resource, request.user, overwrite_bag=False)
        resource_keywords = [subject.value.lower() for subject in resource.metadata.subjects.all()]
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'added_keywords': keywords, 'resource_keywords': resource_keywords,
                              'message': "Add was successful"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Keyword already exists"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def delete_keyword_metadata(request, hs_file_type, file_type_id, **kwargs):
    """deletes a keyword for a given logical file
    The keyword to be deleted is expected as part of the request.POST
    NOTE: This view function must be called via ajax call
    """

    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)

    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    keyword = request.POST['keyword']
    existing_keywords = [kw.lower() for kw in logical_file.metadata.keywords]
    if keyword.lower() in existing_keywords:
        logical_file.metadata.keywords = [kw for kw in logical_file.metadata.keywords if
                                          kw.lower() != keyword.lower()]
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'deleted_keyword': keyword,
                              'message': "Add was successful"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Keyword was not found"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_dataset_name(request, hs_file_type, file_type_id, **kwargs):
    """updates the dataset_name (title) attribute of the specified logical file object
    """

    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'datatset_name', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    dataset_name = request.POST['dataset_name']
    logical_file.dataset_name = dataset_name
    logical_file.save()
    logical_file.metadata.is_dirty = True
    logical_file.metadata.save()
    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'datatset_name', 'message': "Update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_netcdf_file(request, file_type_id, **kwargs):
    """updates (writes the metadata) the netcdf file associated with a instance of a specified
    NetCDFLogicalFile file object
    """

    hs_file_type = "NetCDFLogicalFile"
    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'datatset_name', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    try:
        logical_file.update_netcdf_file(request.user)
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': ex.message}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'message': "NetCDF file update was successful"}
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

    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
    if json_response is not None:
        return json_response

    try:
        if metadata_mode == 'view':
            metadata = logical_file.metadata.get_html()
        else:
            metadata = logical_file.metadata.get_html_forms()
        ajax_response_data = {'status': 'success', 'metadata': metadata}
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': ex.message}

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
