import glob
import json
import os

import jsonschema
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import Error
from django.http import JsonResponse, HttpResponse
from django.template import Context, Template
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError as RF_ValidationError
from rest_framework.response import Response

from hs_core.hydroshare import METADATA_STATUS_SUFFICIENT, METADATA_STATUS_INSUFFICIENT, \
    ResourceFile, utils, delete_resource_file_only
from hs_core.hydroshare.utils import resource_modified
from hs_core.task_utils import get_or_create_task_notification
from hs_core.tasks import FILE_TYPE_MAP, move_aggregation_task
from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize, get_coverage_data_dict
from . import serializers
from .forms import ModelInstanceMetadataValidationForm, ModelProgramMetadataValidationForm
from .utils import set_logical_file_type


class BadRequestException(Exception):
    pass


def authorize_for_aggregation_edit(f=None, file_type=None):
    """a decorator for checking if the user has edit permission to the resource for which the aggregation needs to
    be edited"""

    def real_decorator(view_func):
        def wrapper(request, *args, **kwargs):
            file_type_id = kwargs['file_type_id']
            if file_type == 'NestedLogicalFile':
                hs_file_type = 'FileSetLogicalFile'
                logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
                if logical_file is None:
                    hs_file_type = 'ModelInstanceLogicalFile'
                    logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)
            else:
                hs_file_type = kwargs.get('hs_file_type', file_type)
                logical_file, json_response = _get_logical_file(hs_file_type, file_type_id)

            if json_response is not None:
                return json_response

            resource_id = logical_file.resource.short_id
            resource, authorized, _ = authorize(request, resource_id,
                                                needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                                raises_exception=False)
            ajax_response_data = {}
            if not authorized:
                ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                                      'message': "Permission denied"}

            kwargs['logical_file'] = logical_file
            kwargs['error_response'] = ajax_response_data
            return view_func(request, *args, **kwargs)

        return wrapper

    if f is None:
        return real_decorator
    return real_decorator(f)


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
    folder_path = ''
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
        err_msg = "Aggregation type can be set only for files in a resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    try:
        set_logical_file_type(res, request.user, file_id, hs_file_type, folder_path)
        resource_modified(res, request.user, overwrite_bag=False)

        msg = "{} was successfully set to the selected aggregation type."
        if not folder_path:
            msg = msg.format("Selected file")
        else:
            msg = msg.format("Selected folder")

        response_data['status'] = 'success'
        response_data['message'] = msg
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)

    except ValidationError as ex:
        response_data['message'] = str(ex)
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
    except Exception as ex:
        response_data['message'] = str(ex)
        return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_res_file(pk, file_path):

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
        res_file = ResourceFile.get(resource, file_name, folder)
    except (ValidationError, ObjectDoesNotExist):
        return Response('File {} does not exist.'.format(file_path),
                        status=status.HTTP_400_BAD_REQUEST)

    return res_file


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
    if hs_file_type == "FileSet":
        # call the internal api for setting the file type
        json_response = set_file_type(request=request, resource_id=pk, hs_file_type=hs_file_type)
    else:
        res_file = get_res_file(pk, file_path)
        if isinstance(res_file, Response):
            return res_file

        # call the internal api for setting the file type
        json_response = set_file_type(request=request, resource_id=pk, file_id=res_file.id,
                                      hs_file_type=hs_file_type)

    # only return the message part of the above response
    response_dict = json.loads(json_response.content)
    return Response(data=response_dict['message'],
                    status=json_response.status_code)


def get_fileset_id(resource_id, file_path):
    resource = utils.get_resource_by_shortkey(resource_id)
    filesets = resource.get_logical_files("FileSetLogicalFile")
    filesets = [fs for fs in filesets if fs.folder == file_path]
    if not filesets:
        return Response('Folder {} does not exist.'.format(file_path),
                        status=status.HTTP_400_BAD_REQUEST)

    return filesets[0].id


@api_view(['POST'])
def remove_aggregation_public(request, resource_id, hs_file_type, file_path, **kwargs):
    """Deletes an instance of a specific file type (aggregation) and all the associated metadata.
    However, it doesn't delete resource files associated with the aggregation.
    """
    if hs_file_type == "FileSetLogicalFile":
        fileset_id = get_fileset_id(resource_id, file_path)
        return remove_aggregation(request, resource_id=resource_id, hs_file_type=hs_file_type, file_type_id=fileset_id)
    else:
        res_file = get_res_file(resource_id, file_path)
        if isinstance(res_file, Response):
            return res_file
        return remove_aggregation(request, resource_id=resource_id, hs_file_type=hs_file_type,
                                  file_type_id=res_file.logical_file.id)


@api_view(['DELETE'])
def delete_aggregation_public(request, resource_id, hs_file_type, file_path, **kwargs):
    """Deletes all files associated with an aggregation and all the associated metadata.
    """
    if hs_file_type == "FileSetLogicalFile":
        fileset_id = get_fileset_id(resource_id, file_path)
        return delete_aggregation(request, resource_id=resource_id, hs_file_type=hs_file_type, file_type_id=fileset_id)
    else:
        res_file = get_res_file(resource_id, file_path)
        if isinstance(res_file, Response):
            return res_file
        return delete_aggregation(request, resource_id=resource_id, hs_file_type=hs_file_type,
                                  file_type_id=res_file.logical_file.id)


@api_view(['POST'])
def move_aggregation_public(request, resource_id, hs_file_type, file_path, tgt_path="", **kwargs):
    """moves all files associated with an aggregation and all the associated metadata.
    """
    res_file = get_res_file(resource_id, file_path)
    if isinstance(res_file, Response):
        return res_file

    return move_aggregation(request, resource_id=resource_id, hs_file_type=hs_file_type,
                            file_type_id=res_file.logical_file.id, tgt_path=tgt_path)


@swagger_auto_schema(method="get", responses={200: serializers.ModelProgramMetaTemplateSchemaSerializer})
@api_view(['GET'])
def list_model_program_template_metadata_schemas(request, **kwargs):
    """Returns a list of available template metadata schema filenames for model program aggregation."""

    schema_templates = []
    template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
    template_path = os.path.join(template_path, "*.json")
    for schema_template in glob.glob(template_path):
        template_file_name = os.path.basename(schema_template)
        schema_templates.append({"meta_schema_filename": template_file_name})
    return JsonResponse(schema_templates, safe=False)


@swagger_auto_schema(method='get', responses={200: "Metadata template schema as JSON",
                                              400: "Not a valid metadata template schema filename"})
@api_view(['GET'])
def get_model_program_template_metadata_schema(request, schema_filename, **kwargs):
    """Returns JSON of the specified template metadata schema for model program aggregation."""

    template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
    template_path = os.path.join(template_path, "*.json")
    schema_template_path = ''
    for schema_template in glob.glob(template_path):
        template_schema_filename = os.path.basename(schema_template)
        if template_schema_filename == schema_filename:
            schema_template_path = schema_template
            break

    if schema_template_path:
        with open(schema_template_path) as file_obj:
            schema_data = file_obj.read()
            json_schema = json.loads(schema_data)
            return JsonResponse(json_schema, safe=False)

    return JsonResponse(data=f"{schema_filename} is not a valid metadata template schema filename", safe=False,
                        status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(method='put', responses={204: "Template metadata schema was assigned to model program aggregation",
                                              400: "Invalid/bad request message",
                                              403: "You don't have permission to edit this resource"},)
@api_view(['PUT'])
def use_template_metadata_schema_for_model_program(request, resource_id, aggregation_path, schema_filename, **kwargs):
    """Assigns the specified template metadata schema as the metadata schema for a model program aggregation."""

    try:
        resource, aggr = _validate_model_aggregation_meta_api_request(request=request, resource_id=resource_id,
                                                                      aggregation_path=aggregation_path,
                                                                      model_type='model-program')
    except BadRequestException as ex:
        return JsonResponse(data=str(ex), safe=False, status=status.HTTP_400_BAD_REQUEST)

    template_path = settings.MODEL_PROGRAM_META_SCHEMA_TEMPLATE_PATH
    template_path = os.path.join(template_path, "*.json")
    schema_template_path = ''
    for schema_template in glob.glob(template_path):
        template_schema_filename = os.path.basename(schema_template)
        if template_schema_filename == schema_filename:
            schema_template_path = schema_template
            break

    if not schema_template_path:
        return JsonResponse(data=f"{schema_filename} is not a valid metadata template schema filename", safe=False,
                            status=status.HTTP_400_BAD_REQUEST)
    with open(schema_template_path) as file_obj:
        schema_data = file_obj.read()
        json_schema = json.loads(schema_data)
        aggr.metadata_schema_json = json_schema
        aggr.save()
        aggr.metadata.is_dirty = True
        aggr.metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)

    msg = f"Template schema:{schema_filename} was set as the metadata schema for model program " \
          f"aggregation:{aggregation_path}."
    return JsonResponse(data=msg, safe=False, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='put', responses={204: "Metadata schema was updated for model instance aggregation",
                                              400: "Invalid/bad request message",
                                              403: "You don't have permission to edit this resource"},)
@api_view(['PUT'])
def update_metadata_schema_for_model_instance(request, resource_id, aggregation_path, **kwargs):
    """Updates metadata schema for a model instance aggregation using the schema from the linked
    model program aggregation."""

    try:
        resource, aggr = _validate_model_aggregation_meta_api_request(request=request, resource_id=resource_id,
                                                                      aggregation_path=aggregation_path,
                                                                      model_type='model-instance')
    except BadRequestException as ex:
        return JsonResponse(data=str(ex), safe=False, status=status.HTTP_400_BAD_REQUEST)

    if not aggr.metadata.executed_by:
        err_msg = f"Specified model instance aggregation:{aggregation_path} is not executed by a " \
                  f"model program aggregation"
        return JsonResponse(data=err_msg, safe=False, status=status.HTTP_400_BAD_REQUEST)

    mp_aggr = aggr.metadata.executed_by
    if not mp_aggr.metadata_schema_json:
        err_msg = "Metadata schema is missing for the linked model program aggregation"
        return JsonResponse(data=err_msg, safe=False, status=status.HTTP_400_BAD_REQUEST)

    aggr.metadata_schema_json = mp_aggr.metadata_schema_json
    aggr.save()
    aggr.metadata.is_dirty = True
    aggr.metadata.save()
    resource_modified(resource, request.user, overwrite_bag=False)
    msg = f"Metadata schema was updated for model instance aggregation:{aggregation_path} from the " \
          f"linked model program aggregation."
    return JsonResponse(data=msg, safe=False, status=status.HTTP_204_NO_CONTENT)


@swagger_auto_schema(method='get', operation_description="Gets metadata for a model program aggregation in json",
                     responses={200: serializers.ModelProgramMetaSerializer, 400: "Invalid/bad request message",
                                403: "You don't have permission to view this resource"},)
@swagger_auto_schema(method='put', operation_description="Updates metadata for a model program aggregation",
                     request_body=serializers.ModelProgramMetaSerializer,
                     responses={200: serializers.ModelProgramMetaSerializer, 400: "Invalid/bad request message",
                                403: "You don't have permission to edit this resource"},)
@api_view(['GET', 'PUT'])
def model_program_metadata_in_json(request, resource_id, aggregation_path, **kwargs):
    try:
        resource, aggr = _validate_model_aggregation_meta_api_request(request=request, resource_id=resource_id,
                                                                      aggregation_path=aggregation_path,
                                                                      model_type='model-program')
    except BadRequestException as ex:
        return JsonResponse(data=str(ex), safe=False, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'GET':
        meta_serializer = serializers.ModelProgramMetaSerializer()
        # return the metadata for the model program aggregation
        return JsonResponse(data=meta_serializer.serialize(mp_aggr=aggr), status=status.HTTP_200_OK)

    meta_serializer = serializers.ModelProgramMetaSerializer(data=request.data, context={'mp_aggr': aggr}, partial=True)
    if not meta_serializer.is_valid():
        raise RF_ValidationError(detail=meta_serializer.errors)

    # update model program aggregation metadata
    meta_serializer.update(mp_aggr=aggr, validated_data=meta_serializer.validated_data)

    resource_modified(resource, request.user, overwrite_bag=False)
    # return the metadata for the model program aggregation
    return JsonResponse(data=meta_serializer.serialize(mp_aggr=aggr), status=status.HTTP_200_OK)


@swagger_auto_schema(method='get', operation_description="Gets metadata for a model instance aggregation in json",
                     responses={200: serializers.ModelInstanceMetaSerializer, 400: "Invalid/bad request message",
                                403: "You don't have permission to view this resource"},)
@swagger_auto_schema(method='put', request_body=serializers.ModelInstanceMetaSerializer,
                     operation_description="Updates metadata for a model instance aggregation",
                     responses={200: serializers.ModelInstanceMetaSerializer, 400: "Invalid/bad request message",
                                403: "You don't have permission to edit this resource"},)
@api_view(['GET', 'PUT'])
def model_instance_metadata_in_json(request, resource_id, aggregation_path, **kwargs):
    try:
        resource, aggr = _validate_model_aggregation_meta_api_request(request=request, resource_id=resource_id,
                                                                      aggregation_path=aggregation_path,
                                                                      model_type='model-instance')
    except BadRequestException as ex:
        return JsonResponse(data=str(ex), safe=False, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        meta_serializer = serializers.ModelInstanceMetaSerializer()
        # return the metadata for the model instance aggregation
        return JsonResponse(data=meta_serializer.serialize(mi_aggr=aggr), status=status.HTTP_200_OK)

    meta_serializer = serializers.ModelInstanceMetaSerializer(data=request.data,
                                                              context={'mi_aggr': aggr, 'resource': resource},
                                                              partial=True)
    if not meta_serializer.is_valid():
        raise RF_ValidationError(detail=meta_serializer.errors)

    # update model program instance aggregation metadata
    meta_serializer.update(mi_aggr=aggr, validated_data=meta_serializer.validated_data)

    resource_modified(resource, request.user, overwrite_bag=False)
    # return the metadata for the model instance aggregation
    return JsonResponse(data=meta_serializer.serialize(mi_aggr=aggr), status=status.HTTP_200_OK)


@authorize_for_aggregation_edit
@login_required
def remove_aggregation(request, resource_id, hs_file_type, file_type_id, **kwargs):
    """Deletes an instance of a specific file type (aggregation) and all the associated metadata.
    However, it doesn't delete resource files associated with the aggregation.
    """

    response_data = {'status': 'error'}
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    aggregation = kwargs['logical_file']

    res = aggregation.resource
    if res.resource_type != "CompositeResource":
        err_msg = "Aggregation type can be deleted only in a resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if hs_file_type not in FILE_TYPE_MAP:
        err_msg = "Unsupported aggregation type. Supported aggregation types are: {}"
        err_msg = err_msg.format(list(FILE_TYPE_MAP.keys()))
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    aggregation.remove_aggregation()
    msg = "Aggregation was successfully removed."
    response_data['status'] = 'success'
    response_data['message'] = msg
    spatial_coverage_dict = get_coverage_data_dict(res)
    response_data['spatial_coverage'] = spatial_coverage_dict
    return JsonResponse(response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit
@login_required
def delete_aggregation(request, resource_id, hs_file_type, file_type_id, **kwargs):
    """Deletes all files associated with an aggregation and all the associated metadata.
    """

    response_data = {'status': 'error'}
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    aggregation = kwargs['logical_file']

    if hs_file_type not in FILE_TYPE_MAP:
        err_msg = "Unsupported aggregation type. Supported aggregation types are: {}"
        err_msg = err_msg.format(list(FILE_TYPE_MAP.keys()))
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    aggregation.logical_delete(request.user)
    res = aggregation.resource
    msg = "Aggregation was successfully deleted."
    response_data['status'] = 'success'
    response_data['message'] = msg
    spatial_coverage_dict = get_coverage_data_dict(res)
    response_data['spatial_coverage'] = spatial_coverage_dict
    return JsonResponse(response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit
@login_required
def move_aggregation(request, resource_id, hs_file_type, file_type_id, tgt_path="", run_async=True, **kwargs):
    """
    moves all files associated with an aggregation and all the associated metadata.
    Note that test parameter is added for testing this view function which will not do async move. By default,
    it is set to False, which will do async aggregation move
    """
    response_data = {'status': 'error'}
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_200_OK)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    aggregation = kwargs['logical_file']

    if hs_file_type not in FILE_TYPE_MAP:
        err_msg = "Unsupported aggregation type. Supported aggregation types are: {}"
        err_msg = err_msg.format(list(FILE_TYPE_MAP.keys()))
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    res = aggregation.resource
    if res.resource_type != "CompositeResource":
        err_msg = "Aggregation type can be deleted only in a resource."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    tgt_path = tgt_path.strip()
    if tgt_path:
        tgt_model_aggr = res.get_model_aggregation_in_path(tgt_path)
        src_model_aggr = res.get_model_aggregation_in_path(aggregation.aggregation_name)
        src_fileset_aggr = res.get_fileset_aggregation_in_path(aggregation.aggregation_name)
        move_allowed = True
        if tgt_model_aggr is not None:
            if tgt_model_aggr.is_model_program:
                move_allowed = False
            if tgt_model_aggr.is_model_instance:
                if src_model_aggr is not None and src_model_aggr.is_model_program:
                    move_allowed = False
                if src_fileset_aggr is not None:
                    move_allowed = False

            if not move_allowed:
                err_msg = "This aggregation move is not allowed by the target."
                response_data['message'] = err_msg
                return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    file_override = request.POST.get('file_override', False)
    if not isinstance(file_override, bool):
        file_override = True if str(file_override).lower() == 'true' else False

    # check if files already exist in the target path
    res_files = []
    override_tgt_paths = []
    override_tgt_res_files = []
    file_type_class = FILE_TYPE_MAP[hs_file_type]
    aggregation = file_type_class.objects.get(id=file_type_id)
    res_files.extend(aggregation.files.all())
    istorage = res.get_s3_storage()
    for file in res_files:
        file_name = os.path.basename(file.storage_path)
        if tgt_path:
            tgt_full_path = os.path.join(res.file_path, tgt_path, file_name)
        else:
            tgt_full_path = os.path.join(res.file_path, file_name)
        if istorage.exists(tgt_full_path):
            override_tgt_paths.append(tgt_full_path)
            try:
                override_tgt_res_files.append(ResourceFile.get(res, file=file_name, folder=tgt_path))
            except ObjectDoesNotExist:
                return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    if override_tgt_paths:
        if not file_override:
            override_file_names = ', '.join([os.path.basename(otgt_path) for otgt_path in override_tgt_paths])
            message = f'aggregation move would overwrite {override_file_names}'
            return HttpResponse(message, status=status.HTTP_300_MULTIPLE_CHOICES)
        # delete conflicting files so that move can succeed
        for override_file in override_tgt_res_files:
            delete_resource_file_only(res, override_file)
        res.cleanup_aggregations()

    if run_async:
        task = move_aggregation_task.apply_async((resource_id, file_type_id, hs_file_type, tgt_path))
        task_id = task.task_id
        task_dict = get_or_create_task_notification(task_id, name='aggregation move', payload=resource_id,
                                                    username=request.user.username)
        resource_modified(res, request.user, overwrite_bag=False)
        return JsonResponse(task_dict)
    else:
        move_aggregation_task(resource_id, file_type_id, hs_file_type, tgt_path)
        resource_modified(res, request.user, overwrite_bag=False)
        msg = "Aggregation was successfully moved to {}.".format(tgt_path)
        response_data['status'] = 'success'
        response_data['message'] = msg
        return JsonResponse(response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type='NestedLogicalFile')
@login_required
def update_aggregation_coverage(request, file_type_id, coverage_type, **kwargs):
    """Updates nested (e.g., fileset, model instance) aggregation level coverage using coverage data from the contained
    aggregations
    :param  file_type_id:   id of the nested aggregation for which coverage needs to be updated
    :param  coverage_type:  a value of either temporal or spatial
    """
    response_data = {'status': 'error'}
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    ns_aggr = kwargs['logical_file']

    if coverage_type.lower() not in ('temporal', 'spatial'):
        err_msg = "Invalid coverage type specified."
        response_data['message'] = err_msg
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)

    if coverage_type.lower() == 'spatial':
        ns_aggr.update_spatial_coverage()
        coverage_element = ns_aggr.metadata.spatial_coverage
    else:
        ns_aggr.update_temporal_coverage()
        coverage_element = ns_aggr.metadata.temporal_coverage

    msg = "Aggregation {} coverage was updated successfully.".format(coverage_type.lower())
    response_data['status'] = 'success'
    response_data['message'] = msg
    if coverage_type.lower() == 'spatial':
        response_data['spatial_coverage'] = get_coverage_data_dict(ns_aggr)
    else:
        response_data['temporal_coverage'] = get_coverage_data_dict(ns_aggr, 'temporal')
    response_data['element_id'] = coverage_element.id
    response_data['logical_file_id'] = ns_aggr.id
    response_data['logical_file_type'] = ns_aggr.type_name()
    return JsonResponse(response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit
@login_required
def update_metadata_element(request, hs_file_type, file_type_id, element_name,
                            element_id, **kwargs):
    err_msg = "Failed to update metadata element '{}'. {}."
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = element_name
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_update_success = False
    resource = logical_file.resource
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            logical_file.metadata.update_element(element_name, element_id, **element_data_dict)
            resource_modified(resource, request.user, overwrite_bag=False)
            is_update_success = True
        except ValidationError as ex:
            err_msg = err_msg.format(element_name, str(ex))
        except Error as ex:
            err_msg = err_msg.format(element_name, str(ex))
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

        element = logical_file.metadata.get_element(element_name, element_id)
        update_file = _is_update_file(logical_file, element_name, element)
        if update_file:
            logical_file.metadata.is_update_file = True
            logical_file.metadata.save()

        ajax_response_data['is_update_file'] = update_file

        if logical_file.type_name() == "TimeSeriesLogicalFile":
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


@authorize_for_aggregation_edit
@login_required
def add_metadata_element(request, hs_file_type, file_type_id, element_name, **kwargs):
    err_msg = "Failed to create metadata element '{}'. {}."

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = element_name
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']

    validation_response = logical_file.metadata.validate_element_data(request, element_name)
    is_add_success = False
    resource = logical_file.resource
    if validation_response['is_valid']:
        element_data_dict = validation_response['element_data_dict']
        try:
            element = logical_file.metadata.create_element(element_name, **element_data_dict)
            resource_modified(resource, request.user, overwrite_bag=False)
            is_add_success = True
        except ValidationError as ex:
            err_msg = err_msg.format(element_name, str(ex))
        except Error as ex:
            err_msg = err_msg.format(element_name, str(ex))
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

        update_file = _is_update_file(logical_file, element_name, element)
        if update_file:
            logical_file.metadata.is_update_file = True
            logical_file.metadata.save()

        ajax_response_data['is_update_file'] = update_file

        if logical_file.type_name() == "TimeSeriesLogicalFile":
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


@authorize_for_aggregation_edit
@login_required
def delete_coverage_element(request, hs_file_type, file_type_id,
                            element_id, **kwargs):
    """This function is to delete coverage metadata for single file aggregation or file set
    aggregation"""

    element_type = 'coverage'
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = element_type
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']

    if hs_file_type not in ('GenericLogicalFile', 'FileSetLogicalFile', 'ModelInstanceLogicalFile', 'CSVLogicalFile'):
        err_msg = "Coverage can be deleted only for single file content, model instance content, or file set content."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    coverage_element = logical_file.metadata.coverages.filter(id=element_id).first()
    if coverage_element is None:
        ajax_response_data = {'status': 'error',
                              'logical_file_type': logical_file.type_name(),
                              'element_name': element_type,
                              'message': "No matching coverage was found"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    # delete the coverage element
    logical_file.metadata.delete_element(element_type, element_id)
    resource = logical_file.resource
    if resource.can_be_public_or_discoverable:
        metadata_status = METADATA_STATUS_SUFFICIENT
    else:
        metadata_status = METADATA_STATUS_INSUFFICIENT

    ajax_response_data = {'status': 'success', 'element_name': element_type,
                          'metadata_status': metadata_status,
                          'logical_file_type': logical_file.type_name(),
                          'logical_file_id': logical_file.id
                          }

    spatial_coverage_dict = get_coverage_data_dict(resource)
    temporal_coverage_dict = get_coverage_data_dict(resource, coverage_type='temporal')
    ajax_response_data['spatial_coverage'] = spatial_coverage_dict
    ajax_response_data['temporal_coverage'] = temporal_coverage_dict

    ajax_response_data['has_logical_spatial_coverage'] = \
        resource.has_logical_spatial_coverage
    ajax_response_data['has_logical_temporal_coverage'] = \
        resource.has_logical_temporal_coverage

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit
@login_required
def update_key_value_metadata(request, hs_file_type, file_type_id, **kwargs):
    """add/update key/value additional metadata for a given logical file
    key/value data is expected as part of the request.POST data for adding
    key/value/key_original is expected as part of the request.POST data for updating
    If the key already exists, the value then gets updated, otherwise, the key/value is added
    to the hstore dict type field
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'key_value'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']

    def validate_key():
        if key in list(logical_file.metadata.extra_metadata.keys()):
            ajax_response_data = {'status': 'error',
                                  'logical_file_type': logical_file.type_name(),
                                  'message': "Update failed. Key already exists."}
            return False, JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)
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
                if key_original in list(logical_file.metadata.extra_metadata.keys()):
                    del logical_file.metadata.extra_metadata[key_original]
    else:
        # user trying to add a new pair of key/value
        is_valid, json_response = validate_key()
        if not is_valid:
            return json_response

    logical_file.metadata.extra_metadata[key] = value
    logical_file.metadata.is_dirty = True
    if logical_file.type_name() == "NetCDFLogicalFile":
        logical_file.metadata.is_update_file = True
    logical_file.metadata.save()
    resource = logical_file.resource
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


@authorize_for_aggregation_edit
@login_required
def delete_key_value_metadata(request, hs_file_type, file_type_id, **kwargs):
    """deletes one pair of key/value additional metadata for a given logical file
    key data is expected as part of the request.POST data
    If key is found the matching key/value pair is deleted from the hstore dict type field
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'key_value'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']

    key = request.POST['key']
    resource = logical_file.resource
    if key in list(logical_file.metadata.extra_metadata.keys()):
        del logical_file.metadata.extra_metadata[key]
        logical_file.metadata.is_dirty = True
        if logical_file.type_name() == "NetCDFLogicalFile":
            logical_file.metadata.is_update_file = True
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


@authorize_for_aggregation_edit
@login_required
def add_keyword_metadata(request, hs_file_type, file_type_id, **kwargs):
    """adds one or more keywords for a given logical file
    data for keywords is expected as part of the request.POST
    multiple keywords are part of the post data in a comma separated format
    If any of the keywords to be added already exists (case insensitive check) then none of
    the posted keywords is added
    NOTE: This view function must be called via ajax call
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'keyword'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword',
                              'message': "Editing of keywords is not allowed for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_keywords_in_json:
        # if there are keywords in json file, we don't allow adding new keyword
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message':
                                  "Adding of keyword is not allowed"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    keywords = request.POST['keywords']
    keywords = keywords.split(",")
    existing_keywords = [kw.lower() for kw in logical_file.metadata.keywords]

    if not any(kw.lower() in keywords for kw in existing_keywords):
        metadata = logical_file.metadata
        metadata.keywords += keywords
        if hs_file_type != "TimeSeriesLogicalFile":
            metadata.is_dirty = True
        if hs_file_type == "NetCDFLogicalFile":
            metadata.is_update_file = True
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
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)


@authorize_for_aggregation_edit
@login_required
def delete_keyword_metadata(request, hs_file_type, file_type_id, **kwargs):
    """deletes a keyword for a given logical file
    The keyword to be deleted is expected as part of the request.POST
    NOTE: This view function must be called via ajax call
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'keyword'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_keywords_in_json:
        # if there are keywords in json file, we don't allow deleting keyword
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Keyword delete is not allowed"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword',
                              'message': "Editing of keywords is not allowed for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    keyword = request.POST['keyword']
    existing_keywords = [kw.lower() for kw in logical_file.metadata.keywords]
    if keyword.lower() in existing_keywords:
        logical_file.metadata.keywords = [kw for kw in logical_file.metadata.keywords if
                                          kw.lower() != keyword.lower()]
        if hs_file_type != "TimeSeriesLogicalFile":
            metadata = logical_file.metadata
            metadata.is_dirty = True
            if hs_file_type == "NetCDFLogicalFile":
                metadata.is_update_file = True
            metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'deleted_keyword': keyword,
                              'message': "Add was successful"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'keyword', 'message': "Keyword was not found"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)


@authorize_for_aggregation_edit
@login_required
def update_dataset_name(request, hs_file_type, file_type_id, **kwargs):
    """updates the dataset_name (title) attribute of the specified logical file object
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'dataset_name'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'dataset_name',
                              'message': "Editing of dataset name is not allowed for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    if hs_file_type == "RefTimeseriesLogicalFile" and logical_file.metadata.has_title_in_json:
        # if json file has title, we can't update title (dataset name)
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'title', 'message': "Title can't be updated"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    dataset_name = request.POST['dataset_name']
    logical_file.dataset_name = dataset_name
    logical_file.save()
    metadata = logical_file.metadata
    metadata.is_dirty = True
    if hs_file_type in ("NetCDFLogicalFile", "TimeSeriesLogicalFile"):
        metadata.is_update_file = True
    metadata.save()
    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'dataset_name', "is_dirty": metadata.is_dirty,
                          'message': "Update was successful"}
    if logical_file.type_name() == "TimeSeriesLogicalFile":
        ajax_response_data['can_update_sqlite'] = logical_file.can_update_sqlite_file

    ajax_response_data['is_update_file'] = False
    if hs_file_type in ("NetCDFLogicalFile", "TimeSeriesLogicalFile"):
        ajax_response_data['is_update_file'] = metadata.is_update_file

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type='RefTimeseriesLogicalFile')
@login_required
def update_refts_abstract(request, file_type_id, **kwargs):
    """updates the abstract for ref time series specified logical file object
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'abstract'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract',
                              'message': "Editing of abstract is not allowed for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    if logical_file.metadata.has_abstract_in_json:
        # if json file has abstract, we can't update abstract
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Permission denied"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    abstract = request.POST['abstract']

    if abstract.strip():
        logical_file.metadata.abstract = abstract
        logical_file.metadata.is_dirty = True
        logical_file.metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Update was successful"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Data is missing for abstract"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)


@authorize_for_aggregation_edit(file_type='TimeSeriesLogicalFile')
@login_required
def update_timeseries_abstract(request, file_type_id, **kwargs):
    """updates the abstract for time series specified logical file object
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        error_response['element_name'] = 'abstract'
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract',
                              'message': "Editing of abstract is not allowed for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    abstract = request.POST['abstract']
    if abstract.strip():
        metadata = logical_file.metadata
        metadata.abstract = abstract
        metadata.is_dirty = True
        metadata.is_update_file = True
        metadata.save()
        resource_modified(resource, request.user, overwrite_bag=False)
        ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', "is_dirty": metadata.is_dirty,
                              'can_update_sqlite': logical_file.can_update_sqlite_file,
                              'is_update_file': metadata.is_update_file,
                              'message': "Update was successful"}
    else:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'element_name': 'abstract', 'message': "Data is missing for abstract"}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="NetCDFLogicalFile")
@login_required
def update_netcdf_file(request, file_type_id, **kwargs):
    """updates (writes the metadata) the netcdf file associated with a instance of a specified
    NetCDFLogicalFile file object
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': "NetCDF file can't be updated for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)
    try:
        logical_file.update_netcdf_file(request.user)
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': str(ex)}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'message': "NetCDF file update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="TimeSeriesLogicalFile")
@login_required
def update_sqlite_file(request, file_type_id, **kwargs):
    """updates (writes the metadata) the SQLite file associated with a instance of a specified
    TimeSeriesLogicalFile file object
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    resource = logical_file.resource
    if resource.raccess.published:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': "SQLite file can't be updated for a published resource"}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    try:
        logical_file.update_sqlite_file(request.user)
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': str(ex)}
        return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'message': "SQLite file update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="ModelProgramLogicalFile")
@login_required
def update_model_program_metadata(request, file_type_id, **kwargs):
    """adds/update any/all the following metadata attributes associated metadata object

    """
    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    metadata = logical_file.metadata
    mp_validation_form = ModelProgramMetadataValidationForm(request.POST, request.FILES)
    if not mp_validation_form.is_valid():
        err_messages = []
        for fld in mp_validation_form.errors.keys():
            err_message = mp_validation_form.errors[fld][0]
            err_messages.append({fld: err_message})

        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': err_messages}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    mp_validation_form.update_metadata(metadata)
    refresh_metadata = len(mp_validation_form.cleaned_data['mi_json_schema_file']) > 0 \
        or len(mp_validation_form.cleaned_data['mi_json_schema_template']) > 0

    resource = logical_file.resource
    resource_modified(resource, request.user, overwrite_bag=False)
    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'multiple-elements', 'refresh_metadata': refresh_metadata,
                          'message': "Update was successful"}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="ModelInstanceLogicalFile")
@login_required
def update_model_instance_metadata_json(request, file_type_id, **kwargs):
    """adds/updates the 'metadata_json' field of the associated metadata object. This metadata field stores
    json data based on the metadata json schema of the linked model program.
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    metadata = logical_file.metadata
    metadata_json_str = request.POST['metadata_json']
    try:
        metadata_json = json.loads(metadata_json_str)
    except ValueError as ex:
        msg = "Data is not in JSON format. {}".format(str(ex))
        error_response = {"status": "error", "message": msg}
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # validate json data against metadata schema:
    try:
        metadata_json_schema = logical_file.metadata_schema_json
        jsonschema.Draft4Validator(metadata_json_schema).validate(metadata_json)
    except jsonschema.ValidationError as ex:
        schema_err_msg = "{}. Schema invalid field path:{}".format(str(ex), str(list(ex.path)))
        msg = "JSON metadata is not valid as per the associated metadata schema. Error: {}".format(schema_err_msg)
        error_response = {"status": "error", "message": msg}
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
    # save json data
    metadata.metadata_json = metadata_json
    metadata.is_dirty = True
    metadata.save()
    resource = logical_file.resource
    resource_modified(resource, request.user, overwrite_bag=False)

    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'metadata_json', 'message': "Update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="ModelInstanceLogicalFile")
@login_required
def update_model_instance_meta_schema(request, file_type_id, **kwargs):
    """copies the metadata schema from the associated model program aggregation over to the model instance aggregation
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    metadata = logical_file.metadata
    if not metadata.executed_by:
        msg = "No associated model program was found"
        error_response = {"status": "error", "message": msg}
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
    elif not metadata.executed_by.metadata_schema_json:
        msg = "Associated model program has no metadata schema"
        error_response = {"status": "error", "message": msg}
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)
    logical_file.metadata_schema_json = metadata.executed_by.metadata_schema_json
    if metadata.metadata_json:
        # validate json data against metadata schema:
        try:
            metadata_json_schema = logical_file.metadata_schema_json
            jsonschema.Draft4Validator(metadata_json_schema).validate(metadata.metadata_json)
        except jsonschema.ValidationError:
            # delete existing invalid metadata
            metadata.metadata_json = {}

    logical_file.save()
    metadata.is_dirty = True
    metadata.save()
    resource = logical_file.resource
    resource_modified(resource, request.user, overwrite_bag=False)

    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'metadata_schema_json', 'message': "Update was successful"}
    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="ModelInstanceLogicalFile")
@login_required
def update_model_instance_metadata(request, file_type_id, **kwargs):
    """adds/update any/all of the following metadata attributes associated metadata object
    has_model_output
    executed_by
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    metadata = logical_file.metadata
    current_executed_by = metadata.executed_by
    mi_validation_form = ModelInstanceMetadataValidationForm(request.POST, user=request.user,
                                                             resource=logical_file.resource)

    if not mi_validation_form.is_valid():
        err_messages = []
        for fld in mi_validation_form.errors.keys():
            err_message = mi_validation_form.errors[fld][0]
            err_messages.append({fld: err_message})
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': err_messages}

        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    mi_validation_form.update_metadata(metadata)
    new_executed_by = metadata.executed_by
    resource = logical_file.resource
    resource_modified(resource, request.user, overwrite_bag=False)
    refresh_metadata = current_executed_by != new_executed_by

    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'multiple-elements', 'refresh_metadata': refresh_metadata,
                          'message': "Update was successful"}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


@authorize_for_aggregation_edit(file_type="CSVLogicalFile")
@login_required
def update_csv_table_schema_metadata(request, file_type_id, **kwargs):
    """Updates the tableSchema metadata field of the CSVFileMetadata object associated with the CSVLogicalFile
    """

    # Note: decorator 'authorise_for_aggregation_edit' sets the error_response key in kwargs
    if 'error_response' in kwargs and kwargs['error_response']:
        error_response = kwargs['error_response']
        return JsonResponse(error_response, status=status.HTTP_400_BAD_REQUEST)

    # Note: decorator 'authorise_for_aggregation_edit' sets the logical_file key in kwargs
    logical_file = kwargs['logical_file']
    metadata = logical_file.metadata
    post_table_schema_data = request.POST.dict()
    table_schema_model = metadata.get_table_schema_model()
    for col_no, col in enumerate(table_schema_model.table.columns):
        col.titles = post_table_schema_data[f"column-{col_no}-titles"].strip()
        if col.titles == '':
            col.titles = None
        col.description = post_table_schema_data[f"column-{col_no}-description"].strip()
        if col.description == '':
            col.description = None
        col.datatype = post_table_schema_data[f"column-{col_no}-datatype"].strip()

    # it is not allowed to have some columns with titles and some without titles
    columns_with_titles = [col.titles for col in table_schema_model.table.columns if col.titles]
    if 0 < len(columns_with_titles) < len(table_schema_model.table.columns):
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': "The title for one or more columns is missing."}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    columns_with_duplicate_titles = set([title.lower() for title in columns_with_titles])
    if len(columns_with_duplicate_titles) < len(columns_with_titles):
        ajax_response_data = {'status': 'error', 'logical_file_type': logical_file.type_name(),
                              'message': "Duplicate column titles are not allowed."}
        return JsonResponse(ajax_response_data, status=status.HTTP_400_BAD_REQUEST)

    metadata.tableSchema = table_schema_model.model_dump()
    metadata.is_dirty = True
    metadata.save()
    resource = logical_file.resource
    resource_modified(resource, request.user, overwrite_bag=False)

    ajax_response_data = {'status': 'success', 'logical_file_type': logical_file.type_name(),
                          'element_name': 'multiple-elements', 'refresh_metadata': False,
                          'message': "Update was successful"}

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
    authorize(request, logical_file.resource.short_id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

    if json_response is not None:
        return json_response

    try:
        if metadata_mode == 'view':
            metadata = logical_file.metadata.get_html()
        else:
            metadata = logical_file.metadata.get_html_forms(user=request.user)
        ajax_response_data = {'status': 'success', 'metadata': metadata}
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': str(ex)}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


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

    authorize(request, logical_file.resource.short_id, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)

    series_ids = logical_file.metadata.series_ids_with_labels
    if series_id not in list(series_ids.keys()):
        # this will happen only in case of CSV file upload when data is written
        # first time to the blank sqlite file as the series ids get changed to
        # uuids
        series_id = list(series_ids.keys())[0]
    try:
        if resource_mode == 'view':
            metadata = logical_file.metadata.get_html(series_id=series_id)
        else:
            metadata = logical_file.metadata.get_html_forms(series_id=series_id)
        ajax_response_data = {'status': 'success', 'metadata': metadata}
    except Exception as ex:
        ajax_response_data = {'status': 'error', 'message': str(ex)}

    return JsonResponse(ajax_response_data, status=status.HTTP_200_OK)


def _get_logical_file(hs_file_type, file_type_id):
    try:
        content_type = ContentType.objects.get(app_label="hs_file_types", model=hs_file_type.lower())
    except ObjectDoesNotExist:
        err_msg = "Invalid aggregation type name:{}.".format(hs_file_type)
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return None, JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    logical_file_type_class = content_type.model_class()
    logical_file = logical_file_type_class.objects.filter(id=file_type_id).first()
    if logical_file is None:
        err_msg = "No matching aggregation type was found."
        ajax_response_data = {'status': 'error', 'message': err_msg}
        return None, JsonResponse(ajax_response_data, status=status.HTTP_200_OK)

    return logical_file, None


def _is_update_file(logical_file, element_name, element):
    update_file = False
    if logical_file.type_name() == "NetCDFLogicalFile":
        # only spatial coverage update does not need update of the nc file
        if element_name.lower() != 'coverage':
            update_file = True
        elif element.type == 'period':
            update_file = True
    elif logical_file.type_name() == "TimeSeriesLogicalFile":
        update_file = True
    return update_file


def _validate_model_aggregation_meta_api_request(request, resource_id, aggregation_path, model_type):
    if request.method == 'GET':
        needed_permission = ACTION_TO_AUTHORIZE.VIEW_METADATA
        permission_denied_msg = "You do not have permission to view metadata for this resource."
    else:
        needed_permission = ACTION_TO_AUTHORIZE.EDIT_RESOURCE
        permission_denied_msg = "You do not have permission to edit this resource."

    resource, authorized, user = authorize(
        request, resource_id,
        needed_permission=needed_permission,
        raises_exception=False)

    if not authorized:
        raise PermissionDenied(permission_denied_msg)

    if resource.resource_type != "CompositeResource":
        raise BadRequestException(f"Specified type:{resource_id} is not a resource.")

    # validate aggregation_path
    try:
        aggr = resource.get_aggregation_by_name(aggregation_path)
    except ObjectDoesNotExist:
        err_msg = f"Specified aggregation:{aggregation_path} was not found in resource:{resource_id}"
        raise BadRequestException(err_msg)

    if model_type == 'model-program':
        if not aggr.is_model_program:
            err_msg = f"Specified aggregation:{aggregation_path} is not a model program aggregation"
            raise BadRequestException(err_msg)
    elif not aggr.is_model_instance:
        err_msg = f"Specified aggregation:{aggregation_path} is not a model instance aggregation"
        raise BadRequestException(err_msg)

    return resource, aggr
