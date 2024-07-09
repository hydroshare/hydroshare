import json
import logging
import os

from django.core.exceptions import SuspiciousFileOperation, ValidationError, ObjectDoesNotExist
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest

from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound, status, PermissionDenied, \
    ValidationError as DRF_ValidationError
from rest_framework.response import Response

from django_irods.icommands import SessionException
from hs_core.hydroshare import delete_resource_file
from hs_core.hydroshare.utils import get_file_mime_type, resolve_request, QuotaException
from hs_core.models import ResourceFile
from hs_core.task_utils import get_or_create_task_notification
from hs_core.tasks import FileOverrideException, unzip_task
from hs_core.views import utils as view_utils

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE, zip_folder, unzip_file, \
    create_folder, remove_folder, move_or_rename_file_or_folder, move_to_folder, \
    rename_file_or_folder, irods_path_is_directory, \
    add_reference_url_to_resource, edit_reference_url_in_resource, zip_by_aggregation_file

from hs_file_types.models import FileSetLogicalFile, ModelInstanceLogicalFile, ModelProgramLogicalFile

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


logger = logging.getLogger(__name__)


def data_store_structure(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in hydroshareZone or any federated zone used for HydroShare resource backend store.
    It is invoked by an AJAX call and returns json object that holds content for files
    and folders under the requested directory/collection/subcollection.
    The AJAX request must be a POST request with input data passed in for res_id and store_path
    where store_path is the relative path to res_id/data/contents
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        logger.error("no resource id in request")
        return HttpResponse('Bad request - resource id is not included',
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    except NotFound:
        logger.error("resource {} not found".format(res_id))
        return HttpResponse('Bad request - resource not found', status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        logger.error("permission denied for resource {}".format(res_id))
        return HttpResponse('Permission denied', status=status.HTTP_401_UNAUTHORIZED)

    store_path = request.POST.get('store_path', None)

    try:
        store_path = _validate_path(store_path, check_path_empty=False)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    istorage = resource.get_irods_storage()
    directory_in_irods = resource.get_irods_path(store_path)

    try:
        store = istorage.listdir(directory_in_irods)
    except SessionException as ex:
        logger.error("session exception querying store_path {} for {}".format(store_path, res_id))
        return HttpResponse(ex.stderr, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    files = []
    dirs = []
    aggregations = []
    _APPKEY = 'appkey'
    # folder path relative to 'data/contents/' needed for the UI
    folder_path = store_path[len("data/contents/"):]
    if resource.resource_type == "CompositeResource":
        res_aggregations = list(resource.logical_files)

    for dname in store[0]:     # directories
        d_pk = dname
        d_store_path = os.path.join(store_path, d_pk)
        d_url = resource.get_url_of_path(d_store_path)
        main_file = ''
        folder_aggregation_type = ''
        folder_aggregation_name = ''
        folder_aggregation_id = ''
        folder_aggregation_type_to_set = ''
        folder_aggregation_appkey = ''
        if resource.resource_type == "CompositeResource":
            dir_path = resource.get_irods_path(d_store_path)
            # find if this folder *dir_path* represents (contains) an aggregation object
            aggregation_object = resource.get_folder_aggregation_object(dir_path, aggregations=res_aggregations)
            # folder aggregation type is not relevant for single file aggregation types - which
            # are: GenericLogicalFile, and RefTimeseriesLogicalFile
            if aggregation_object is not None:
                folder_aggregation_type = aggregation_object.get_aggregation_class_name()
                folder_aggregation_name = aggregation_object.get_aggregation_display_name()
                folder_aggregation_id = aggregation_object.id
                folder_aggregation_appkey = aggregation_object.metadata.extra_metadata.get(_APPKEY, '')
                aggr_main_file = aggregation_object.get_main_file
                if aggr_main_file is not None:
                    main_file = aggr_main_file.file_name
            else:
                # check first if ModelProgram/ModelInstance aggregation type can be created from this folder
                can_set_model_instance = ModelInstanceLogicalFile.can_set_folder_to_aggregation(
                    resource=resource, dir_path=dir_path, aggregations=res_aggregations)
                can_set_model_program = ModelProgramLogicalFile.can_set_folder_to_aggregation(
                    resource=resource, dir_path=dir_path, aggregations=res_aggregations)
                if can_set_model_instance and can_set_model_program:
                    folder_aggregation_type_to_set = 'ModelProgramOrInstanceLogicalFile'
                elif can_set_model_program:
                    folder_aggregation_type_to_set = ModelProgramLogicalFile.__name__
                elif can_set_model_instance:
                    folder_aggregation_type_to_set = ModelInstanceLogicalFile.__name__
                # otherwise, check if FileSet aggregation type that can be created from this folder
                elif FileSetLogicalFile.can_set_folder_to_aggregation(resource=resource, dir_path=dir_path,
                                                                      aggregations=res_aggregations):
                    folder_aggregation_type_to_set = FileSetLogicalFile.__name__
                else:
                    folder_aggregation_type_to_set = ""
        dirs.append({'name': d_pk,
                     'url': d_url,
                     'main_file': main_file,
                     'folder_aggregation_type': folder_aggregation_type,
                     'folder_aggregation_name': folder_aggregation_name,
                     'folder_aggregation_id': folder_aggregation_id,
                     'folder_aggregation_type_to_set': folder_aggregation_type_to_set,
                     'folder_short_path': os.path.join(folder_path, d_pk),
                     'folder_aggregation_appkey': folder_aggregation_appkey,
                     })

    for index, fname in enumerate(store[1]):  # files
        f_store_path = os.path.join(store_path, fname)
        file_in_irods = resource.get_irods_path(f_store_path)
        res_file = ResourceFile.objects.filter(object_id=resource.id,
                                               resource_file=file_in_irods).first()

        if not res_file:
            # skip metadata files
            continue

        size = store[2][index]
        mtype = get_file_mime_type(fname)
        idx = mtype.find('/')
        if idx >= 0:
            mtype = mtype[idx + 1:]

        f_ref_url = ''
        logical_file_type = ''
        logical_file_id = ''
        aggregation_name = ''
        # flag for UI to know if a file is part of a model program aggregation that has been created from a folder
        # Note: model program aggregation can be created either from a single file of a folder that has one or more
        # files
        has_model_program_aggr_folder = False
        has_model_instance_aggr_folder = False
        aggregation_appkey = ''
        if res_file.has_logical_file:
            main_extension = res_file.logical_file.get_main_file_type()
            if not main_extension:
                # accept any extension
                main_extension = ""

            _ , file_extension = os.path.splitext(fname)
            if file_extension and main_extension.endswith(file_extension):
                if not hasattr(res_file.logical_file, 'folder') or res_file.logical_file.folder is None:
                    aggregation_appkey = res_file.logical_file.metadata.extra_metadata.get(_APPKEY, '')

                aggregations.append({'logical_file_id': res_file.logical_file.id,
                                     'name': res_file.logical_file.dataset_name,
                                     'logical_type': res_file.logical_file.get_aggregation_class_name(),
                                     'aggregation_name': res_file.logical_file.get_aggregation_display_name(),
                                     'aggregation_appkey': aggregation_appkey,
                                     'main_file': res_file.logical_file.get_main_file.file_name,
                                     'preview_data_url': res_file.logical_file.metadata.get_preview_data_url(
                                         resource=resource,
                                         folder_path=f_store_path
                                     ),
                                     'url': res_file.logical_file.url})
            logical_file = res_file.logical_file
            logical_file_type = res_file.logical_file_type_name
            logical_file_id = logical_file.id
            aggregation_name = res_file.aggregation_display_name
            aggregation_appkey = ''
            if not hasattr(logical_file, 'folder') or logical_file.folder is None:
                aggregation_appkey = logical_file.metadata.extra_metadata.get(_APPKEY, '')
            if 'url' in res_file.logical_file.extra_data:
                f_ref_url = res_file.logical_file.extra_data['url']

            # check if this file (f) is part of a model program folder aggregation
            if logical_file_type == "ModelProgramLogicalFile":
                if res_file.file_folder is not None and res_file.logical_file.folder is not None:
                    if res_file.file_folder.startswith(res_file.logical_file.folder):
                        has_model_program_aggr_folder = True
            elif logical_file_type == "ModelInstanceLogicalFile":
                if res_file.file_folder is not None and res_file.logical_file.folder is not None:
                    if res_file.file_folder.startswith(res_file.logical_file.folder):
                        has_model_instance_aggr_folder = True

        files.append({'name': fname, 'size': size, 'type': mtype, 'pk': res_file.pk, 'url': res_file.url,
                      'reference_url': f_ref_url,
                      'aggregation_name': aggregation_name,
                      'logical_type': logical_file_type,
                      'logical_file_id': logical_file_id,
                      'aggregation_appkey': aggregation_appkey,
                      'has_model_program_aggr_folder': has_model_program_aggr_folder,
                      'has_model_instance_aggr_folder': has_model_instance_aggr_folder})

    return_object = {'files': files,
                     'folders': dirs,
                     'aggregations': aggregations,
                     'can_be_public': resource.can_be_public_or_discoverable}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def to_external_url(url):
    """
    Convert an internal download file/folder url to the external url.  This should eventually be
    replaced with a reverse method that gets the correct mapping.
    """
    return url.replace("django_irods/download", "resource", 1)


def data_store_folder_zip(request, res_id=None):
    """
    Zip requested files and folders into a zip file in hydroshareZone or any federated zone
    used for HydroShare resource backend store. It is invoked by an AJAX call and returns
    json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The AJAX request must be a POST request with input data passed in for
    res_id, input_coll_path, output_zip_file_name, and remove_original_after_zip where
    input_coll_path is the relative path under res_id/data/contents to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name,
    and remove_original_after_zip has a value of "true" or "false" (default is "true") indicating
    whether original files will be deleted after zipping.
    """
    res_id = request.POST.get('res_id', res_id)
    if res_id is None:
        return JsonResponse({"error": "Resource id was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    input_coll_path = resolve_request(request).get('input_coll_path', None)

    try:
        input_coll_path = _validate_path(input_coll_path)
    except ValidationError as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    output_zip_fname = resolve_request(request).get('output_zip_file_name', None)
    if output_zip_fname is None:
        return JsonResponse({"error": "Output zip file name was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    output_zip_fname = str(output_zip_fname).strip()
    if not output_zip_fname:
        return JsonResponse({"error": "Output zip file name can't be be empty string"},
                            status=status.HTTP_400_BAD_REQUEST)

    remove_original = resolve_request(request).get('remove_original_after_zip', None)
    bool_remove_original = True
    if remove_original is not None:
        remove_original = str(remove_original).strip().lower()
        if remove_original == 'false':
            bool_remove_original = False

    try:
        output_zip_fname, size = \
            zip_folder(user, res_id, input_coll_path, output_zip_fname, bool_remove_original)
    except SessionException as ex:
        return JsonResponse({"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except DRF_ValidationError as ex:
        return JsonResponse({"error": ex.detail}, status=status.HTTP_400_BAD_REQUEST)
    except (QuotaException) as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    return_data = {"name": output_zip_fname, "size": size, "type": "zip"}
    return JsonResponse(return_data)


def zip_aggregation_file(request, res_id=None):
    """
    Zip requested aggregation into a zip file in hydroshareZone or any federated zone
    used for HydroShare resource backend store. It is invoked by an AJAX call and returns
    json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The AJAX request must be a POST request with input data passed in for
    res_id, aggregation_path, and output_zip_file_name where
    aggregation_path  is the relative path under res_id/data/contents representing an aggregation to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name.
    """
    res_id = request.POST.get('res_id', res_id)
    if res_id is None:
        return JsonResponse({"error": "Resource id was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    if resource.resource_type != "CompositeResource":
        err_msg = f"{resource.display_name} type doesn't support zipping of aggregation."
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    aggregation_path = resolve_request(request).get('aggregation_path', None)

    try:
        aggregation_path = _validate_path(aggregation_path)
    except ValidationError as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    output_zip_fname = resolve_request(request).get('output_zip_file_name', None)
    if output_zip_fname is None:
        return JsonResponse({"error": "Output zip filename was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    output_zip_fname = str(output_zip_fname).strip()
    if not output_zip_fname:
        return JsonResponse({"error": "Output zip filename can't be empty"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        output_zip_fname, size = zip_by_aggregation_file(user, res_id, aggregation_path, output_zip_fname)
    except SessionException as ex:
        return JsonResponse({"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except DRF_ValidationError as ex:
        return JsonResponse({"error": ex.detail}, status=status.HTTP_400_BAD_REQUEST)
    except (QuotaException) as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    return_data = {"name": output_zip_fname, "size": size, "type": "zip"}
    return JsonResponse(return_data)


rid = openapi.Parameter('id', openapi.IN_PATH, description="id of the resource", type=openapi.TYPE_STRING)
body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'input_coll_path': openapi.Schema(type=openapi.TYPE_STRING, description='the relative path under res_id/data/ \
            contents to be zipped'),
        'output_zip_file_name': openapi.Schema(type=openapi.TYPE_STRING, description='the file name only with no path \
            of the generated zip file name'),
        'remove_original_after_zip': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='whether original files \
            will be deleted after zipping')
    }
)


@swagger_auto_schema(method='post',
                     operation_description="Zip requested files and folders into a zip file",
                     responses={200: "Returns JsonResponse with zip file or empty string"},
                     manual_parameters=[rid], request_body=body)
@api_view(['POST'])
def data_store_folder_zip_public(request, pk):
    '''
    Zip requested files and folders into a zip file in hydroshareZone or any federated zone

    Used for HydroShare resource backend store. Returns
    json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The request must be a POST request with input data passed in for
    **res_id, input_coll_path, output_zip_file_name, and remove_original_after_zip** where
    input_coll_path is the relative path under res_id/data/contents to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name,
    and remove_original_after_zip has a value of "true" or "false" (default is "true") indicating
    whether original files will be deleted after zipping.

    :param request:
    :param pk: Id of the hydroshare resource
    :return: JsonResponse with zip file or empty string
    '''
    return data_store_folder_zip(request, res_id=pk)


rid = openapi.Parameter('id', openapi.IN_PATH, description="id of the resource", type=openapi.TYPE_STRING)
body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'aggregation_path': openapi.Schema(type=openapi.TYPE_STRING, description='the relative path under res_id/data/ \
            contents to be zipped'),
        'output_zip_file_name': openapi.Schema(type=openapi.TYPE_STRING, description='the file name only with no path \
            of the generated zip file name')
    }
)


@swagger_auto_schema(method='post', operation_description="Zip requested aggregation into a zip file in hydroshareZone \
                                                            or any federated zone",
                     responses={200: "Returns JsonResponse with zip file or empty string"},
                     manual_parameters=[rid], request_body=body)
@api_view(['POST'])
def zip_aggregation_file_public(request, pk):
    '''
    Zip requested aggregation into a zip file in hydroshareZone or any federated zone

    Used for HydroShare resource backend store.
    Returns a json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The request must be a POST request with input data passed in for
    **res_id, aggregation_path, and output_zip_file_name** where
    aggregation_path  is the relative path under res_id/data/contents representing an aggregation to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name.

    :param request:
    :return: JsonResponse with zip file or empty string
    '''
    return zip_aggregation_file(request, res_id=pk)


def data_store_folder_unzip(request, **kwargs):
    """
    Unzip requested zip file while preserving folder structures in hydroshareZone or
    any federated zone used for HydroShare resource backend store. It is invoked by an AJAX call,
    and returns json object that holds the root path that contains the zipped content if it
    succeeds, and an empty string if it fails. The AJAX request must be a POST request with
    input data passed in for res_id, zip_with_rel_path, and remove_original_zip where
    zip_with_rel_path is the zip file name with relative path under res_id collection to be
    unzipped, and remove_original_zip has a value of "true" or "false" (default is "true")
    indicating whether original zip file will be deleted after unzipping.
    """
    res_id = request.POST.get('res_id', kwargs.get('res_id'))
    if res_id is None:
        return JsonResponse({"error": "Resource id was not provided"}, status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    zip_with_rel_path = request.POST.get('zip_with_rel_path', kwargs.get('zip_with_rel_path'))

    try:
        zip_with_rel_path = _validate_path(zip_with_rel_path)
    except ValidationError as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    overwrite = request.POST.get('overwrite', 'false').lower() == 'true'  # False by default
    auto_aggregate = request.POST.get('auto_aggregate', 'true').lower() == 'true'  # True by default
    ingest_metadata = request.POST.get('ingest_metadata', 'false').lower() == 'true'  # False by default
    remove_original_zip = request.POST.get('remove_original_zip', 'true').lower() == 'true'
    unzip_to_folder = request.POST.get('unzip_to_folder', 'false').lower() == 'true'

    if request.is_ajax():
        task = unzip_task.apply_async((user.pk, res_id, zip_with_rel_path, remove_original_zip, overwrite,
                                       auto_aggregate, ingest_metadata, unzip_to_folder))
        task_id = task.task_id
        task_dict = get_or_create_task_notification(task_id, name='file unzip', username=request.user.username,
                                                    payload=resource.get_absolute_url())
        return JsonResponse(task_dict)
    else:
        try:
            unzip_file(user, res_id, zip_with_rel_path, remove_original_zip, overwrite, auto_aggregate,
                       ingest_metadata, unzip_to_folder)
        except SessionException as ex:
            specific_msg = "iRODS error resulted in unzip being cancelled. This may be due to " \
                           "protection from overwriting existing files. Unzip in a different " \
                           "location (e.g., folder) or move or rename the file being overwritten. " \
                           "iRODS error follows: "
            err_msg = specific_msg + ex.stderr
            return JsonResponse({"error": err_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except (DRF_ValidationError, SuspiciousFileOperation, FileOverrideException, QuotaException) as ex:
            err_msg = ex.detail if isinstance(ex, DRF_ValidationError) else str(ex)
            return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            err_msg = str(ex)
            return JsonResponse({"error": err_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # this unzipped_path can be used for POST request input to data_store_structure()
        # to list the folder structure after unzipping
        return_data = {'unzipped_path': os.path.dirname(zip_with_rel_path)}
        return JsonResponse(return_data)


@api_view(['POST'])
def data_store_folder_unzip_public(request, pk, pathname):
    """
    Public version of data_store_folder_unzip, incorporating path variables

    :param request:
    :param pk:
    :param pathname:
    :return HttpResponse:
    """

    return data_store_folder_unzip(request, res_id=pk, zip_with_rel_path=pathname)


rid = openapi.Parameter('id', openapi.IN_PATH, description="id of the resource", type=openapi.TYPE_STRING)


@swagger_auto_schema(method='post', operation_description="Ingests metadata files",
                     responses={204: "HttpResponse response with status code"},
                     manual_parameters=[rid])
@api_view(['POST'])
def ingest_metadata_files(request, pk):
    '''
    Ingests metadata files

    The files to be ingested should be provided in the REST request

    :param request:
    :param pk: id of the hydroshare resource
    :return: HttpResponse response with status code
    '''
    from hs_file_types.utils import identify_and_ingest_metadata_files
    resource, _, _ = view_utils.authorize(request, pk,
                                          needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    resource_files = list(request.FILES.values())
    identify_and_ingest_metadata_files(resource, resource_files)
    return Response(status=204)


body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'res_id': openapi.Schema(type=openapi.TYPE_STRING, description='res_id'),
        'curr_path': openapi.Schema(type=openapi.TYPE_STRING, description='curr_path'),
        'ref_name': openapi.Schema(type=openapi.TYPE_STRING, description='ref_name'),
        'ref_url': openapi.Schema(type=openapi.TYPE_STRING, description='ref_url')
    }
)


@swagger_auto_schema(method='post', operation_description="Create reference URL file",
                     responses={200: "JsonResponse with status code and message"}, request_body=body)
@api_view(['POST'])
def data_store_add_reference_public(request):
    """
    Create the reference url file, add the url file to resource, and add the url to
    metadata accordingly for easy later retrieval
    Request should include **curr_path**, **res_id**, **ref_name**, and **ref_url**
    :param request:
    :return: JsonResponse with status code and message
    """
    return data_store_add_reference(request._request)


@swagger_auto_schema(method='post', auto_schema=None)
@api_view(['POST'])
def data_store_add_reference(request):
    """
    create the reference url file, add the url file to resource, and add the url to
    metadata accordingly for easy later retrieval
    :param request:
    :return: JsonResponse with status code and message
    """

    res_id = request.POST.get('res_id', None)
    curr_path = request.POST.get('curr_path', None)
    ref_name = request.POST.get('ref_name', None)
    ref_url = request.POST.get('ref_url', None)
    validate_url_flag = request.POST.get('validate_url_flag', 'true')
    validate_url_flag = True if validate_url_flag.lower() == 'true' else False

    if not res_id:
        return HttpResponseBadRequest('Must have res_id included in the POST data')
    if not ref_name:
        return HttpResponseBadRequest('Must have ref_name included in the POST data')
    if not ref_url:
        return HttpResponseBadRequest('Must have ref_url included in the POST data')
    try:
        curr_path = _validate_path(curr_path, check_path_empty=False)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    try:
        res, _, _ = authorize(request, res_id,
                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return HttpResponseBadRequest('Bad request - resource not found')
    except PermissionDenied:
        return HttpResponse('Permission denied', status=status.HTTP_401_UNAUTHORIZED)

    ret_status, msg, file_id = add_reference_url_to_resource(request.user, res_id, ref_url,
                                                             ref_name, curr_path,
                                                             validate_url_flag=validate_url_flag)
    if ret_status == status.HTTP_200_OK:
        return JsonResponse({'status': 'success', 'file_id': file_id})
    else:
        return JsonResponse({'message': msg}, status=ret_status)


body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'res_id': openapi.Schema(type=openapi.TYPE_STRING, description='res_id'),
        'curr_path': openapi.Schema(type=openapi.TYPE_STRING, description='curr_path'),
        'url_filename': openapi.Schema(type=openapi.TYPE_STRING, description='url_filename'),
        'new_ref_url': openapi.Schema(type=openapi.TYPE_STRING, description='new_ref_url')
    }
)


@swagger_auto_schema(method='post', operation_description="Edit the referenced url in a url file",
                     responses={200: "JsonResponse on success", 400: "HttpResponse with error status code on error"},
                     request_body=body)
@api_view(['POST'])
def data_store_edit_reference_url_public(request):
    """
    Edit the referenced url in a url file

    Post request should include **res_id, curr_path, url_filename, new_ref_url**
    :param request:
    :return: JsonResponse on success or HttpResponse with error status code on error
    """
    return data_store_edit_reference_url(request._request)


@swagger_auto_schema(method='post', auto_schema=None)
@api_view(['POST'])
def data_store_edit_reference_url(request):
    """
    edit the referenced url in an url file
    :param request:
    :return: JsonResponse on success or HttpResponse with error status code on error
    """
    res_id = request.POST.get('res_id', None)
    curr_path = request.POST.get('curr_path', None)
    url_filename = request.POST.get('url_filename', None)
    new_ref_url = request.POST.get('new_ref_url', None)
    validate_url_flag = request.POST.get('validate_url_flag', 'true')
    validate_url_flag = True if validate_url_flag.lower() == 'true' else False

    if not res_id:
        return HttpResponseBadRequest('Must have res_id included in the POST data')

    if not url_filename:
        return HttpResponseBadRequest('Must have url_filename included in the POST data')
    if not new_ref_url:
        return HttpResponseBadRequest('Must have new_ref_url included in the POST data')

    try:
        curr_path = _validate_path(curr_path, check_path_empty=False)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    try:
        res, _, _ = authorize(request, res_id,
                              needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return HttpResponseBadRequest('Bad request - resource not found')
    except PermissionDenied:
        return HttpResponse('Permission denied', status=status.HTTP_401_UNAUTHORIZED)

    ret_status, msg = edit_reference_url_in_resource(request.user, res, new_ref_url,
                                                     curr_path, url_filename,
                                                     validate_url_flag=validate_url_flag)
    if ret_status == status.HTTP_200_OK:
        return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'message': msg}, status=ret_status)


def data_store_create_folder(request):
    """
    create a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that has the
    relative path of the new folder created if succeeds, and return empty string if fails. The
    AJAX request must be a POST request with input data passed in for res_id and folder_path
    where folder_path is the relative path to res_id/data/contents for the new folder to be
    created under res_id collection/directory.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return JsonResponse({"error": "Resource id was not specified"}, status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    folder_path = request.POST.get('folder_path', None)

    try:
        folder_path = _validate_path(folder_path)
    except ValidationError as ex:
        return JsonResponse({"error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)

    try:
        create_folder(res_id, folder_path)
    except SessionException as ex:
        return JsonResponse({"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except (DRF_ValidationError, SuspiciousFileOperation) as ex:
        err_msg = ex.detail if isinstance(ex, DRF_ValidationError) else str(ex)
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'new_folder_rel_path': folder_path})


def data_store_remove_folder(request):
    """
    remove a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that include a
    status of 'success' if succeeds, and HttpResponse of status code of 403, 400, or 500 if fails.
    The AJAX request must be a POST request with input data passed in for res_id and folder_path
    where folder_path is the relative path (relative to res_id/data/contents) for the folder to
    be removed under res_id collection/directory.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included',
                            status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return HttpResponse('Bad request - resource not found', status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return HttpResponse('Permission denied', status=status.HTTP_401_UNAUTHORIZED)

    folder_path = request.POST.get('folder_path', None)

    try:
        folder_path = _validate_path(folder_path)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    try:
        remove_folder(user, res_id, folder_path)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as ex:
        return HttpResponse(str(ex), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return_object = {'status': 'success'}
    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_file_or_folder_move_or_rename(request, res_id=None):
    """
    Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that has the
    relative path of the target file or folder being moved to if succeeds, and return empty string
    if fails. The AJAX request must be a POST request with input data passed in for res_id,
    source_path, and target_path where source_path and target_path are the relative paths
    (relative to path res_id/data/contents) for the source and target file or folder under
    res_id collection/directory.
    """
    res_id = request.POST.get('res_id', res_id)
    if res_id is None:
        return JsonResponse({"error": "Resource id was not specified"}, status=status.HTTP_400_BAD_REQUEST)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    src_path = resolve_request(request).get('source_path', None)
    tgt_path = resolve_request(request).get('target_path', None)
    try:
        src_path = _validate_path(src_path)
        tgt_path = _validate_path(tgt_path)
    except ValidationError as ex:
        err_msg = str(ex)
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    try:
        move_or_rename_file_or_folder(user, res_id, src_path, tgt_path)
    except SessionException as ex:
        return JsonResponse({"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except (DRF_ValidationError, ValidationError, SuspiciousFileOperation) as ex:
        err_msg = ex.detail if isinstance(ex, DRF_ValidationError) else str(ex)
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'target_rel_path': tgt_path})


rid = openapi.Parameter('id', openapi.IN_PATH, description="id of the resource", type=openapi.TYPE_STRING)
body = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'source_path': openapi.Schema(type=openapi.TYPE_STRING, description='path (relative to path \
            res_id/data/contents) for source file or folder under id collection'),
        'target_path': openapi.Schema(type=openapi.TYPE_STRING, description='path (relative to path \
            res_id/data/contents) for target file or folder under id collection')
    }
)


@swagger_auto_schema(method='post',
                     operation_description="Move a list of files and/or folders to another folder in a resource file \
                         hierarchy.", manual_parameters=[rid], request_body=body)
@api_view(['POST'])
def data_store_file_or_folder_move_or_rename_public(request, pk):
    """
    Move a list of files and/or folders to another folder in a resource file hierarchy.

    :param request: a REST request
    :param pk: the short_id of a resource to modify, from REST URL.

    Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that has the
    relative path of the target file or folder being moved to if succeeds, and return empty string
    if fails. The AJAX request must be a POST request with input data passed in for **res_id**,
    **source_path**, and **target_path** where source_path and target_path are the relative paths
    (relative to path res_id/data/contents) for the source and target file or folder under
    res_id collection/directory.
    """
    return data_store_file_or_folder_move_or_rename(request, res_id=pk)


@swagger_auto_schema(method='post', auto_schema=None)
@api_view(['POST'])
def data_store_move_to_folder(request, pk=None):
    """
    Move a list of files and/or folders to another folder in a resource file hierarchy.

    :param request: a REST request
    :param pk: the short_id of a resource to modify, from REST URL.

    It is invoked by an AJAX call and returns a json object that has the relative paths of
    the target files or folders to which files have been moved. The AJAX request must be a POST
    request with input data passed in for source_paths and target_path where source_paths
    and target_path are the relative paths (relative to path res_id/data/contents) for the source
    and target file or folder in the res_id file directory.

    This routine is **specifically** targeted at validating requests from the UI.
    Thus it is much more limiting than a general purpose REST responder.
    """
    pk = request.POST.get('res_id', pk)
    if pk is None:
        return HttpResponse('Bad request - resource id is not included',
                            status=status.HTTP_400_BAD_REQUEST)

    pk = str(pk).strip()
    try:
        resource, _, user = authorize(request, pk,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return HttpResponse('Bad request - resource not found', status=status.HTTP_400_BAD_REQUEST)
    except PermissionDenied:
        return HttpResponse('Permission denied', status=status.HTTP_401_UNAUTHORIZED)

    tgt_path = resolve_request(request).get('target_path', None)
    src_paths = resolve_request(request).get('source_paths', None)
    file_override = resolve_request(request).get('file_override', False)
    if not isinstance(file_override, bool):
        file_override = True if str(file_override).lower() == 'true' else False
    try:
        tgt_path = _validate_path(tgt_path, check_path_empty=False)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    istorage = resource.get_irods_storage()

    tgt_short_path = tgt_path[len('data/contents/'):]
    tgt_storage_path = os.path.join(resource.root_path, tgt_path)

    if not irods_path_is_directory(istorage, tgt_storage_path):
        return HttpResponse('Target of move is not an existing folder',
                            status=status.HTTP_400_BAD_REQUEST)

    src_paths = json.loads(src_paths)

    # protect against common hacking attacks
    for index, src_path in enumerate(src_paths):
        try:
            src_paths[index] = _validate_path(src_path)
        except ValidationError as ex:
            return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    valid_src_paths = []
    override_tgt_paths = []

    for src_path in src_paths:
        src_storage_path = os.path.join(resource.root_path, src_path)
        src_short_path = src_path[len('data/contents/'):]

        # protect against stale data botches: source files should exist
        try:
            folder, file = ResourceFile.resource_path_is_acceptable(resource,
                                                                    src_storage_path,
                                                                    test_exists=True)
        except ValidationError:
            return HttpResponse('Source file {} does not exist'.format(src_short_path),
                                status=status.HTTP_400_BAD_REQUEST)

        if not irods_path_is_directory(istorage, src_storage_path):  # there is django record
            try:
                ResourceFile.get(resource, file, folder=folder)
            except ObjectDoesNotExist:
                return HttpResponse('Source file {} does not exist'.format(src_short_path),
                                    status=status.HTTP_400_BAD_REQUEST)

        # protect against inadvertent overwrite
        base = os.path.basename(src_storage_path)
        tgt_overwrite = os.path.join(tgt_storage_path, base)
        if not istorage.exists(tgt_overwrite):
            valid_src_paths.append(src_path)  # partly qualified path for operation
        else:
            override_tgt_paths.append(os.path.join(tgt_short_path, base))
            if file_override:
                valid_src_paths.append(src_path)

    if override_tgt_paths:
        if not file_override:
            message = 'move would overwrite {}'.format(', '.join(override_tgt_paths))
            return HttpResponse(message, status=status.HTTP_300_MULTIPLE_CHOICES)
        # delete conflicting files so that move can succeed
        for override_tgt_path in override_tgt_paths:
            override_storage_tgt_path = os.path.join(resource.root_path, 'data', 'contents', override_tgt_path)
            if irods_path_is_directory(istorage, override_storage_tgt_path):
                # folder rather than a data object, just delete the folder
                remove_folder(user, pk, os.path.join('data', 'contents', override_tgt_path))
            else:
                # data object or file
                delete_resource_file(pk, override_tgt_path, user)
        resource.cleanup_aggregations()

    try:
        move_to_folder(user, pk, valid_src_paths, tgt_path)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except DRF_ValidationError as ex:
        return HttpResponse(ex.detail, status=status.HTTP_400_BAD_REQUEST)

    return_object = {'target_rel_path': tgt_path}

    return HttpResponse(
        json.dumps(return_object),
        content_type='application/json'
    )


@swagger_auto_schema(method='post', auto_schema=None)
@api_view(['POST'])
def data_store_rename_file_or_folder(request, pk=None):
    """
    Rename one file or folder in a resource file hierarchy.  It is invoked by an AJAX call

    :param request: a REST request
    :param pk: the short_id of a resource to modify, from REST URL.

    This is invoked by an AJAX call in the UI. It returns a json object that has the
    relative path of the target file or folder that has been renamed. The AJAX request
    must be a POST request with input data for source_path and target_path, where source_path
    and target_path are the relative paths (relative to path res_id/data/contents) for the
    source and target file or folder.

    This routine is **specifically** targeted at validating requests from the UI.
    Thus it is much more limiting than a general purpose REST responder.
    """
    pk = request.POST.get('res_id', pk)
    if pk is None:
        return JsonResponse({"error": "Resource id was not specified"}, status=status.HTTP_400_BAD_REQUEST)

    pk = str(pk).strip()
    try:
        resource, _, user = authorize(request, pk,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except NotFound:
        return JsonResponse({"error": "Resource was not found"}, status=status.HTTP_400_BAD_REQUEST)

    except PermissionDenied:
        return JsonResponse({"error": "Permission denied"}, status=status.HTTP_401_UNAUTHORIZED)

    src_path = resolve_request(request).get('source_path', None)
    tgt_path = resolve_request(request).get('target_path', None)
    try:
        src_path = _validate_path(src_path)
        tgt_path = _validate_path(tgt_path)
    except ValidationError as ex:
        return HttpResponse(str(ex), status=status.HTTP_400_BAD_REQUEST)

    src_folder, src_base = os.path.split(src_path)
    tgt_folder, tgt_base = os.path.split(tgt_path)

    if src_folder != tgt_folder:
        return JsonResponse({"error": "Source and target names must be in same folder"},
                            status=status.HTTP_400_BAD_REQUEST)
    istorage = resource.get_irods_storage()

    # protect against stale data botches: source files should exist
    src_storage_path = os.path.join(resource.root_path, src_path)
    try:
        folder, base = ResourceFile.resource_path_is_acceptable(resource,
                                                                src_storage_path,
                                                                test_exists=True)
    except ValidationError:
        return JsonResponse({"error": "Object to be renamed does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    if not irods_path_is_directory(istorage, src_storage_path):
        try:  # Django record should exist for each file
            ResourceFile.get(resource, base, folder=folder)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Path to be renamed does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    # check that the target doesn't exist
    tgt_storage_path = os.path.join(resource.root_path, tgt_path)
    tgt_short_path = tgt_path[len('data/contents/'):]
    if istorage.exists(tgt_storage_path):
        err_msg = f"Desired name ({tgt_short_path}) already in use"
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)
    try:
        folder, base = ResourceFile.resource_path_is_acceptable(resource,
                                                                tgt_storage_path,
                                                                test_exists=False)
    except ValidationError:
        err_msg = f"Poorly structured desired name: {tgt_short_path}"
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    try:
        ResourceFile.get(resource, base, folder=tgt_short_path)
        err_msg = f"Desired name ({tgt_short_path}) already in use"
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    except ObjectDoesNotExist:
        pass  # correct response

    try:
        rename_file_or_folder(user, pk, src_path, tgt_path)
    except SessionException as ex:
        return JsonResponse({"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except (DRF_ValidationError, SuspiciousFileOperation) as ex:
        err_msg = ex.detail if isinstance(ex, DRF_ValidationError) else str(ex)
        return JsonResponse({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)

    return JsonResponse({'target_rel_path': tgt_path})


def _validate_path(path, check_path_empty=True):

    if path is None:
        raise ValidationError("A value for path is missing")

    # strip trailing slashes (if any)
    path = str(path).strip().rstrip('/')
    if not path and check_path_empty:
        raise ValidationError('Path cannot be empty')

    if path.startswith('/'):
        raise ValidationError(f"Path ({path}) must not start with '/'")

    if path.find('/../') >= 0 or path.endswith('/..'):
        raise ValidationError(f"Path ({path}) must not contain '/../'")

    if not path:
        path = "data/contents"
    elif not path.startswith('data/contents/'):
        path = os.path.join('data', 'contents', path)
    return path
