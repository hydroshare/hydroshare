import json
import logging
import os

from django.http import HttpResponse
from django.core.exceptions import ValidationError
from rest_framework.exceptions import NotFound, PermissionDenied

from django_irods.icommands import SessionException

from hs_core.hydroshare.utils import get_file_mime_type, get_resource_file_name_and_extension, \
    get_resource_file_url
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE, zip_folder, unzip_file, \
    create_folder, remove_folder, move_or_rename_file_or_folder
from hs_core.models import ResourceFile

logger = logging.getLogger(__name__)


def data_store_structure(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in hydroshareZone or any federated zone used for HydroShare resource backend store.
    It is invoked by an AJAX call and returns json object that holds content for files
    and folders under the requested directory/collection/subcollection.
    The AJAX request must be a POST request with input data passed in for res_id and store_path
    where store_path is the relative path under res_id collection/directory
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)

    store_path = request.POST.get('store_path', None)
    if store_path is None:
        return HttpResponse('Bad request - store_path is not included', status=400)
    store_path = str(store_path).strip()
    if not store_path:
        return HttpResponse('Bad request - store_path cannot be empty', status=400)
    istorage = resource.get_irods_storage()
    if resource.resource_federation_path:
        res_coll = os.path.join(resource.resource_federation_path, res_id, store_path)
        rel_path = store_path
    else:
        res_coll = os.path.join(res_id, store_path)
        rel_path = res_coll
    try:
        store = istorage.listdir(res_coll)
        files = []
        for fname in store[1]:
            name_with_full_path = os.path.join(res_coll, fname)
            name_with_rel_path = os.path.join(rel_path, fname)
            size = istorage.size(name_with_full_path)
            mtype = get_file_mime_type(fname)
            idx = mtype.find('/')
            if idx >= 0:
                mtype = mtype[idx + 1:]
            f_pk = ''
            f_url = ''
            logical_file_type = ''
            logical_file_id = ''
            for f in ResourceFile.objects.filter(object_id=resource.id):
                if name_with_rel_path == get_resource_file_name_and_extension(f)[0]:
                    f_pk = f.pk
                    f_url = get_resource_file_url(f)
                    if resource.resource_type == "CompositeResource":
                        logical_file_type = f.logical_file_type_name
                        logical_file_id = f.logical_file.id
                    break

            files.append({'name': fname, 'size': size, 'type': mtype, 'pk': f_pk, 'url': f_url,
                          'logical_type': logical_file_type, 'logical_file_id': logical_file_id})
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=500)

    return_object = {'files': files,
                     'folders': store[0]}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_folder_zip(request):
    """
    Zip requested files and folders into a zip file in hydroshareZone or any federated zone
    used for HydroShare resource backend store. It is invoked by an AJAX call and returns
    json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The AJAX request must be a POST request with input data passed in for
    res_id, input_coll_path, output_zip_file_name, and remove_original_after_zip where
    input_coll_path is the relative sub-collection path under res_id collection to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name,
    and remove_original_after_zip has a value of "true" or "false" (default is "true") indicating
    whether original files will be deleted after zipping.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)
    input_coll_path = request.POST.get('input_coll_path', None)
    if input_coll_path is None:
        return HttpResponse('Bad request - input_coll_path is not included', status=400)
    input_coll_path = str(input_coll_path).strip()
    if not input_coll_path:
        return HttpResponse('Bad request - input_coll_path cannot be empty', status=400)
    output_zip_fname = request.POST.get('output_zip_file_name', None)
    if output_zip_fname is None:
        return HttpResponse('Bad request - output_zip_fname is not included', status=400)
    output_zip_fname = str(output_zip_fname).strip()
    if not output_zip_fname:
        return HttpResponse('Bad request - output_zip_fname cannot be empty', status=400)
    remove_original = request.POST.get('remove_original_after_zip', None)
    bool_remove_original = True
    if remove_original:
        remove_original = str(remove_original).strip().lower()
        if remove_original == 'false':
            bool_remove_original = False

    try:
        output_zip_fname, size = \
            zip_folder(user, res_id, input_coll_path, output_zip_fname, bool_remove_original)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=500)

    return_object = {'name': output_zip_fname,
                     'size': size,
                     'type': 'zip'}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_folder_unzip(request):
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
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)
    zip_with_rel_path = request.POST.get('zip_with_rel_path', None)
    if zip_with_rel_path is None:
        return HttpResponse('Bad request - zip_with_rel_path is not included', status=400)
    zip_with_rel_path = str(zip_with_rel_path).strip()
    if not zip_with_rel_path:
        return HttpResponse('Bad request - zip_with_rel_path cannot be empty', status=400)
    remove_original = request.POST.get('remove_original_zip', None)
    bool_remove_original = True
    if remove_original:
        remove_original = str(remove_original).strip().lower()
        if remove_original == 'false':
            bool_remove_original = False

    try:
        unzip_file(user, res_id, zip_with_rel_path, bool_remove_original)
    except SessionException as ex:
        specific_msg = "iRODS error resulted in unzip being cancelled. This may be due to " \
                       "protection from overwriting existing files. Unzip in a different " \
                       "location (e.g., folder) or move or rename the file being overwritten. " \
                       "iRODS error follows: "
        return HttpResponse(specific_msg + ex.stderr, status=500)

    # this unzipped_path can be used for POST request input to data_store_structure()
    # to list the folder structure after unzipping
    return_object = {'unzipped_path': os.path.dirname(zip_with_rel_path)}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_create_folder(request):
    """
    create a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that has the
    relative path of the new folder created if succeeds, and return empty string if fails. The
    AJAX request must be a POST request with input data passed in for res_id and folder_path
    where folder_path is the relative path for the new folder to be created under
    res_id collection/directory.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)

    folder_path = request.POST.get('folder_path', None)
    if folder_path is None:
        return HttpResponse('Bad request - folder_path is not included', status=400)
    folder_path = str(folder_path).strip()
    if not folder_path:
        return HttpResponse('Bad request - folder_path cannot be empty', status=400)

    try:
        create_folder(res_id, folder_path)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=500)
    except ValidationError as ex:
        return HttpResponse(ex.message, status=500)

    return_object = {'new_folder_rel_path': folder_path}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_remove_folder(request):
    """
    remove a sub-folder/sub-collection in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that include a
    status of 'success' if succeeds, and HttpResponse of status code of 403, 400, or 500 if fails.
    The AJAX request must be a POST request with input data passed in for res_id and folder_path
    where folder_path is the relative path for the folder to be removed under
    res_id collection/directory.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)

    folder_path = request.POST.get('folder_path', None)
    if folder_path is None:
        return HttpResponse('Bad request - folder_path is not included', status=400)
    folder_path = str(folder_path).strip()
    if not folder_path:
        return HttpResponse('Bad request - folder_path cannot be empty', status=400)

    try:
        remove_folder(user, res_id, folder_path)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=500)

    return_object = {'status': 'success'}
    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )


def data_store_file_or_folder_move_or_rename(request):
    """
    Move or rename a file or folder in hydroshareZone or any federated zone used for HydroShare
    resource backend store. It is invoked by an AJAX call and returns json object that has the
    relative path of the target file or folder being moved to if succeeds, and return empty string
    if fails. The AJAX request must be a POST request with input data passed in for res_id,
    source_path, and target_path where source_path and target_path are the relative paths for the
    source and target file or folder under res_id collection/directory.
    """
    res_id = request.POST.get('res_id', None)
    if res_id is None:
        return HttpResponse('Bad request - resource id is not included', status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, user = authorize(request, res_id,
                                      needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission denied response
        return HttpResponse('Permission denied', status=403)

    src_path = request.POST.get('source_path', None)
    tgt_path = request.POST.get('target_path', None)
    if src_path is None or tgt_path is None:
        return HttpResponse('Bad request - src_path or tgt_path is not included', status=400)
    src_path = str(src_path).strip()
    tgt_path = str(tgt_path).strip()
    if not src_path or not tgt_path:
        return HttpResponse('Bad request - src_path or tgt_path cannot be empty', status=400)

    try:
        move_or_rename_file_or_folder(user, res_id, src_path, tgt_path)
    except SessionException as ex:
        return HttpResponse(ex.stderr, status=500)
    except ValidationError as ex:
        return HttpResponse(ex.message, status=500)

    return_object = {'target_rel_path': tgt_path}

    return HttpResponse(
        json.dumps(return_object),
        content_type='application/json'
    )
