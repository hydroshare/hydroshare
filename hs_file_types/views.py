import os
import json

from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import Error
from django.contrib.contenttypes.models import ContentType
from django.template import Template, Context

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response


from hs_core.hydroshare import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    ResourceFile, utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize, get_coverage_data_dict
from hs_core.hydroshare.utils import resource_modified

from .models import GeoRasterLogicalFile, NetCDFLogicalFile, GeoFeatureLogicalFile, \
    RefTimeseriesLogicalFile, TimeSeriesLogicalFile, GenericLogicalFile

from .utils import set_logical_file_type

FILE_TYPE_MAP = {"GenericLogicalFile": GenericLogicalFile,
                 "GeoRasterLogicalFile": GeoRasterLogicalFile,
                 "NetCDFLogicalFile": NetCDFLogicalFile,
                 "GeoFeatureLogicalFile": GeoFeatureLogicalFile,
                 "RefTimeseriesLogicalFile": RefTimeseriesLogicalFile,
                 "TimeSeriesLogicalFile": TimeSeriesLogicalFile
                 }


@login_required
def set_file_type(request, resource_id, hs_file_type, file_id=None, **kwargs):
    """Set a file (*file_id*) to a specific file type - aggregation (*hs_file_type*)
    :param  request: an instance of HttpRequest
    :param  resource_id: id of the resource in which this file type needs to be set
    :param  file_id: id of the file which needs to be set to a file type. If file_id is not provided
    then the request must have a file_folder key. In that case the specified folder will be used
    for creating the logical file (aggregation)
    :param  hs_file_type: file type to be set (e.g, SingleFile, NetCDF, GeoRaster, RefTimeseries,
    TimeSeries and GeoFeature)
    :return an instance of JsonResponse type
    """

    response_data = {'status': 'error'}
    folder_path = None
    if file_id is None:
        folder_path = request.POST.get('folder_path', "")
        if not folder_path:
            err_msg = "Must provide id of the file or folder path for setting aggregation type."
            response_data['message'] = err_msg
            return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    res, authorized, _ = authorize(request, resource_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                   raises_exception=False)
    response_data = {'status': 'error'}
    if not authorized:
        err_msg = "Permission denied"
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if res.resource_type != "CompositeResource":
        err_msg = "Aggregation type can be set only for files in composite resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        set_logical_file_type(res, request.user, file_id, hs_file_type, folder_path)
        resource_modified(res, request.user, overwrite_bag=False)

        msg = "{} was successfully set to the selected aggregation type."
        if folder_path is None:
            msg = msg.format("Selected file")
        else:
            msg = msg.format("Selected folder")

        response_data['status'] = 'success'
        response_data['message'] = msg
        spatial_coverage_dict = get_coverage_data_dict(res)
        response_data['spatial_coverage'] = spatial_coverage_dict
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)

    except ValidationError as ex:
        response_data['message'] = ex.message
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        response_data['message'] = ex.message
        return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_file_type_public(request, pk, file_path, hs_file_type):
    """
    Set file type as specified by *hs_file_type* using the file given by *file_path*

    :param request: an instance of HttpRequest object
    :param pk: id of the composite resource in which this file type needs to be set
    :param file_path: relative file path of the file which needs to be set to the specified file
    type. If the absolute file path is [resource-id]/data/contents/some-folder/some-file.txt then
    file_path needs to be set as: some-folder/some-file.txt
    :param hs_file_type: type of file to be set (e.g, NetCDF, GeoRaster, GeoFeature etc)
    :return:
    """

    # get id of the file from the file_path to map to the internal api call
    file_rel_path = str(file_path).strip()
    if not file_rel_path:
        return JsonResponse('file_path cannot be empty',
                            status=status.HTTP_400_BAD_REQUEST)

    # security checks deny illicit requests
    if file_rel_path.find('/../') >= 0 or file_rel_path.endswith('/..'):
        return JsonResponse('file_path must not contain /../',
                            status=status.HTTP_400_BAD_REQUEST)

    resource = utils.get_resource_by_shortkey(pk)
    file_storage_path = os.path.join(resource.file_path, file_rel_path)

    try:
        folder, file_name = ResourceFile.resource_path_is_acceptable(resource,
                                                                     file_storage_path,
                                                                     test_exists=True)
    except ValidationError:
        return Response('File {} does not exist.'.format(file_path),
                        status=status.HTTP_400_BAD_REQUEST)

    res_file = ResourceFile.get(resource, file_name, folder)

    # call the internal api for setting the file type
    json_response = set_file_type(request=request, resource_id=pk, file_id=res_file.id,
                                  hs_file_type=hs_file_type)
    # only return the message part of the above response
    response_dict = json.loads(json_response.content)
    return Response(data=response_dict['message'],
                    status=json_response.status_code)


@login_required
def delete_file_type(request, resource_id, hs_file_type, file_type_id, **kwargs):
    """deletes an instance of a specific file type and all its associated resource files"""

    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "CompositeResource":
        err_msg = "Aggregation type can be deleted only in composite resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    if hs_file_type != "GeoRaster":
        err_msg = "Currently only an instance of Geo Raster aggregation type can be deleted."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    logical_file_to_delete = GeoRasterLogicalFile.objects.filter(id=file_type_id).first()
    if logical_file_to_delete is None:
        err_msg = "No matching Geo Raster aggregation type was found."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    if logical_file_to_delete.resource.short_id != res.short_id:
        err_msg = "Geo Raster aggregation type doesn't belong to the specified resource."
        messages.error(request, err_msg)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    logical_file_to_delete.logical_delete(request.user)
    resource_modified(res, request.user, overwrite_bag=False)
    msg = "Geo Raster aggregation type was deleted."
    messages.success(request, msg)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required
def remove_aggregation(request, resource_id, hs_file_type, file_type_id, **kwargs):
    """Deletes an instance of a specific file type (aggregation) and all the associated metadata.
    However, it doesn't delete resource files associated with the aggregation.
    """

    response_data = {'status': 'error'}

    res, _, _ = authorize(request, resource_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    if res.resource_type != "CompositeResource":
        err_msg = "Aggregation type can be deleted only in composite resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if hs_file_type not in FILE_TYPE_MAP:
        err_msg = "Unsupported aggregation type. Supported aggregation types are: {}"
        err_msg = err_msg.format(FILE_TYPE_MAP.keys())
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    aggregation = logical_file_type_class.objects.filter(id=file_type_id).first()
    if aggregation is None:
        err_msg = "No matching aggregation was found."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    aggregation.remove_aggregation()
    msg = "Aggregation was successfully removed."
    response_data['status'] = 'success'
    response_data['message'] = msg
    spatial_coverage_dict = get_coverage_data_dict(res)
    response_data['spatial_coverage'] = spatial_coverage_dict
    return JsonResponse(response_data, status=status.HTTP_200_OK)


@login_required
def update_metadata_element(request, hs_file_type, file_type_id, element_name,
                            element_id, **kwargs):
    err_msg = "Failed to update metadata element '{}'. {}."
    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching aggregation type was found."
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
        if logical_file.type_name() == "TimeSeriesLogicalFile":
            ajax_response_data['is_dirty'] = logical_file.metadata.is_dirty
            ajax_response_data['can_update_sqlite'] = logical_file.can_update_sqlite_file
            if element_name.lower() == 'site':
                # get the updated spatial coverage of the resource
                spatial_coverage_dict = get_coverage_data_dict(resource)
                ajax_response_data['spatial_coverage'] = spatial_coverage_dict

        elif element_name.lower() == 'coverage':
            spatial_coverage_dict = get_coverage_data_dict(resource)
            temporal_coverage_dict = get_coverage_data_dict(resource, coverage_type='temporal')
            ajax_response_data['spatial_coverage'] = spatial_coverage_dict
            ajax_response_data['temporal_coverage'] = temporal_coverage_dict

        ajax_response_data['has_logical_spatial_coverage'] = \
            resource.has_logical_spatial_coverage
        ajax_response_data['has_logical_temporal_coverage'] = \
            resource.has_logical_temporal_coverage

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
        err_msg = "No matching aggregation type was found."
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

        if logical_file.type_name() == "TimeSeriesLogicalFile":
            ajax_response_data['is_dirty'] = logical_file.metadata.is_dirty
            ajax_response_data['can_update_sqlite'] = logical_file.can_update_sqlite_file
            if element_name.lower() == 'site':
                # get the updated spatial coverage of the resource
                spatial_coverage_dict = get_coverage_data_dict(resource)
                ajax_response_data['spatial_coverage'] = spatial_coverage_dict
        elif element_name.lower() == 'coverage':
            spatial_coverage_dict = get_coverage_data_dict(resource)
            temporal_coverage_dict = get_coverage_data_dict(resource, coverage_type='temporal')
            ajax_response_data['spatial_coverage'] = spatial_coverage_dict
            ajax_response_data['temporal_coverage'] = temporal_coverage_dict

        ajax_response_data['has_logical_spatial_coverage'] = resource.has_logical_spatial_coverage
        ajax_response_data['has_logical_temporal_coverage'] = resource.has_logical_temporal_coverage

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

    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_keywords_in_json:
        # if there are keywords in json file, we don't allow adding new keyword
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message':
                                  "Adding of keyword is not allowed"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    keywords = request.POST['keywords']
    keywords = keywords.split(",")
    existing_keywords = [kw.lower() for kw in logical_file.metadata.keywords]
    if not any(kw.lower() in keywords for kw in existing_keywords):
        metadata = logical_file.metadata
        metadata.keywords += keywords
        if hs_file_type != "TimeSeriesLogicalFile":
            metadata.is_dirty = True
        metadata.save()
        # add keywords to resource
        resource_keywords = [subject.value.lower() for subject in resource.metadata.subjects.all()]
        for kw in keywords:
            if kw.lower() not in resource_keywords:
                resource.metadata.create_element('subject', value=kw)
        resource_modified(resource, request.user, overwrite_bag=False)
        resource_keywords = [subject.value for subject in resource.metadata.subjects.all()]
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

    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_keywords_in_json:
        # if there are keywords in json file, we don't allow deleting keyword
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message':
                                  "Keyword delete is not allowed"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

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
        if hs_file_type != "TimeSeriesLogicalFile":
            metadata = logical_file.metadata
            metadata.is_dirty = True
            metadata.save()
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

    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_title_in_json:
        # if json file has title, we can't update title (dataset name)
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'title', 'message': "Title can't be updated"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    dataset_name = request.POST['dataset_name']
    logical_file.dataset_name = dataset_name
    logical_file.save()
    metadata = logical_file.metadata
    metadata.is_dirty = True
    metadata.save()
    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'datatset_name', "is_dirty": metadata.is_dirty,
                          'message': "Update was successful"}
    if logical_file.type_name() == "TimeSeriesLogicalFile":
        ajax_response_data['can_update_sqlite'] = logical_file.can_update_sqlite_file

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_refts_abstract(request, file_type_id, **kwargs):
    """updates the abstract for ref time series specified logical file object
    """

    logical_file, json_response = _get_logical_file('RefTimeseriesLogicalFile', file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    if logical_file.metadata.has_abstract_in_json:
        # if json file has abstract, we can't update abstract
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    abstract = request.POST['abstract']
    if abstract.strip():
        logical_file.metadata.abstract = abstract
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Update was successful"}
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Data is missing for abstract"}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@login_required
def update_timeseries_abstract(request, file_type_id, **kwargs):
    """updates the abstract for time series specified logical file object
    """

    logical_file, json_response = _get_logical_file('TimeSeriesLogicalFile', file_type_id)
    if json_response is not None:
        return json_response

    resource_id = logical_file.resource.short_id
    resource, authorized, _ = authorize(request, resource_id,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    abstract = request.POST['abstract']
    if abstract.strip():
        metadata = logical_file.metadata
        metadata.abstract = abstract
        metadata.is_dirty = True
        metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', "is_dirty": metadata.is_dirty,
                              'can_update_sqlite': logical_file.can_update_sqlite_file,
                              'message': "Update was successful"}
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Data is missing for abstract"}

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
def update_sqlite_file(request, file_type_id, **kwargs):
    """updates (writes the metadata) the SQLite file associated with a instance of a specified
    TimeSeriesLogicalFile file object
    """

    hs_file_type = "TimeSeriesLogicalFile"
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
        logical_file.update_sqlite_file(request.user)
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': ex.message}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'message': "SQLite file update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


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

    from hs_core.views.utils import authorize
    from rest_framework.exceptions import PermissionDenied
    if not logical_file.resource.raccess.public:
        if request.user.is_authenticated:
            authorize(request, logical_file.resource.short_id,
                      needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        else:
            raise PermissionDenied()

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


@login_required
def get_timeseries_metadata(request, file_type_id, series_id, resource_mode):
    """
    Gets metadata html for the aggregation type (logical file type)
    :param request:
    :param file_type_id: id of the aggregation (logical file) object for which metadata in html
    format is needed
    :param  series_id: if of the time series for which metadata to be displayed
    :param resource_mode: a value of either edit or view. In resource edit mode metadata html
    form elements are returned. In view mode normal html for display of metadata is returned
    :return: json data containing html string
    """
    if resource_mode != "edit" and resource_mode != 'view':
        err_msg = "Invalid metadata type request."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    logical_file, json_response = _get_logical_file("TimeSeriesLogicalFile", file_type_id)
    if json_response is not None:
        return json_response

    series_ids = logical_file.metadata.series_ids_with_labels
    if series_id not in series_ids.keys():
        # this will happen only in case of CSV file upload when data is written
        # first time to the blank sqlite file as the series ids get changed to
        # uuids
        series_id = series_ids.keys()[0]
    try:
        if resource_mode == 'view':
            metadata = logical_file.metadata.get_html(series_id=series_id)
        else:
            metadata = logical_file.metadata.get_html_forms(series_id=series_id)
        ajax_response_data = {'status': 'success', 'metadata': metadata}
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': ex.message}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


def _get_logical_file(hs_file_type, file_type_id):
    content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching aggregation type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return None, JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    return logical_file, None
