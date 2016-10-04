import json
import logging
import os

from django.http import HttpResponse
from rest_framework.exceptions import NotFound, PermissionDenied

from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException

from hs_core.hydroshare.utils import get_file_mime_type, get_resource_file_name_and_extension, \
    get_resource_file_url
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import delete_resource_file
from hs_core.models import ResourceFile

logger = logging.getLogger(__name__)


def link_irods_file_to_django(resource, filename, size=0):
    # link the newly created zip file to Django resource model
    if resource:
        if resource.resource_federation_path:
            if not ResourceFile.objects.filter(object_id=resource.id,
                                               fed_resource_file_name_or_path=filename).exists():
                ResourceFile.objects.create(content_object=resource,
                                            resource_file=None,
                                            fed_resource_file_name_or_path=filename,
                                            fed_resource_file_size=size)
        elif not ResourceFile.objects.filter(object_id=resource.id,
                                             resource_file=filename).exists():
                ResourceFile.objects.create(content_object=resource,
                                            resource_file=filename)


def link_irods_folder_to_django(resource, istorage, foldername, exclude=()):
    if resource and istorage and foldername:
        store = istorage.listdir(foldername)
        # add the unzipped files into Django resource model
        for file in store[1]:
            if file not in exclude:
                file_path = os.path.join(foldername, file)
                size = istorage.size(file_path)
                link_irods_file_to_django(resource, file_path, size)
        for folder in store[0]:
            link_irods_folder_to_django(resource,
                                        istorage, os.path.join(foldername, folder), exclude)


def rename_irods_file_in_django(resource, src_name, tgt_name):
    if resource:
        if resource.resource_federation_path:
            res_file_obj = ResourceFile.objects.filter(object_id=resource.id,
                                                       fed_resource_file_name_or_path=src_name)
            if res_file_obj.exists():
                res_file_obj[0].fed_resource_file_name_or_path = tgt_name
                res_file_obj[0].save()
        else:
            res_file_obj = ResourceFile.objects.filter(object_id=resource.id,
                                                       resource_file=src_name)
            if res_file_obj.exists():
                # since resource_file is a FileField which cannot be directly renamed,
                # this old ResourceFile object has to be deleted followed by creation of
                # a new ResourceFile with new file associated that replace the old one
                res_file_obj[0].delete()
                ResourceFile.objects.create(content_object=resource, resource_file=tgt_name)


def data_store_structure(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in hydroshareZone or any federated zone used for HydroShare resource backend store.
    It is invoked by an AJAX call and returns json object that holds content for files
    and folders under the requested directory/collection/subcollection.
    The AJAX request must be a POST request with input data passed in for res_id and store_path
    where store_path is the relative path under res_id collection/directory
    """
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)

    store_path = request.POST['store_path']
    if store_path is None:
        return HttpResponse(status=400)
    store_path = str(store_path).strip()
    if not store_path:
        return HttpResponse(status=400)
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_coll = os.path.join(resource.resource_federation_path, res_id, store_path)
    else:
        istorage = IrodsStorage()
        res_coll = os.path.join(res_id, store_path)

    try:
        store = istorage.listdir(res_coll)
        files = []
        for fname in store[1]:
            name_with_full_path = os.path.join(res_coll, fname)
            size = istorage.size(name_with_full_path)
            mtype = get_file_mime_type(fname)
            idx = mtype.find('/')
            if idx >= 0:
                mtype = mtype[idx + 1:]
            f_pk = ''
            f_url = ''
            for f in ResourceFile.objects.filter(object_id=resource.id):
                if fname == get_resource_file_name_and_extension(f)[1]:
                    f_pk = f.pk
                    f_url = get_resource_file_url(f)
                    break
            files.append({'name': fname, 'size': size, 'type': mtype, 'pk': f_pk, 'url': f_url})
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

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
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)
    input_coll_path = request.POST['input_coll_path']
    if input_coll_path is None:
        return HttpResponse(status=400)
    input_coll_path = str(input_coll_path).strip()
    if not input_coll_path:
        return HttpResponse(status=400)
    output_zip_fname = request.POST['output_zip_file_name']
    if output_zip_fname is None:
        return HttpResponse(status=400)
    output_zip_fname = str(output_zip_fname).strip()
    if not output_zip_fname:
        return HttpResponse(status=400)
    remove_original = request.POST['remove_original_after_zip']
    bool_remove_original = True
    if remove_original:
        remove_original = str(remove_original).strip().lower()
        if remove_original == 'false':
            bool_remove_original = False

    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_coll_input = os.path.join(resource.resource_federation_path, res_id, input_coll_path)
    else:
        istorage = IrodsStorage()
        res_coll_input = os.path.join(res_id, input_coll_path)

    logger.debug("Before: res_coll_input is: " + res_coll_input)
    content_dir = os.path.dirname(res_coll_input)
    logger.debug("After: content_dir: " + content_dir)
    output_zip_full_path = os.path.join(content_dir, output_zip_fname)
    try:
        istorage.session.run("ibun", None, '-cDzip', '-f', output_zip_full_path, res_coll_input)
        size = istorage.size(output_zip_full_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    link_irods_file_to_django(resource, output_zip_full_path, size)

    if bool_remove_original:
        try:
            for f in ResourceFile.objects.filter(object_id=resource.id):
                full_path_name, basename, _ = get_resource_file_name_and_extension(f)
                if res_coll_input in full_path_name:
                    delete_resource_file(res_id, basename, request.user)

            # remove empty folder in iRODS
            istorage.delete(res_coll_input)
        except Exception:
            return HttpResponse(status=500)

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
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)
    zip_with_rel_path = request.POST['zip_with_rel_path']
    if zip_with_rel_path is None:
        return HttpResponse(status=400)
    zip_with_rel_path = str(zip_with_rel_path).strip()
    if not zip_with_rel_path:
        return HttpResponse(status=400)
    remove_original = request.POST['remove_original_zip']
    bool_remove_original = True
    if remove_original:
        remove_original = str(remove_original).strip().lower()
        if remove_original == 'false':
            bool_remove_original = False

    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        zip_with_full_path = os.path.join(resource.resource_federation_path, res_id,
                                          zip_with_rel_path)
    else:
        istorage = IrodsStorage()
        zip_with_full_path = os.path.join(res_id, zip_with_rel_path)

    unzip_path = os.path.dirname(zip_with_full_path)
    zip_fname = os.path.basename(zip_with_rel_path)
    try:
        istorage.session.run("ibun", None, '-xfDzip', zip_with_full_path, unzip_path)
        link_irods_folder_to_django(resource, istorage, unzip_path, (zip_fname,))
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    if bool_remove_original:
        try:
            delete_resource_file(res_id, zip_fname, request.user)
        except Exception:
            return HttpResponse(status=500)

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
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)

    folder_path = request.POST['folder_path']
    if folder_path is None:
        return HttpResponse(status=400)
    folder_path = str(folder_path).strip()
    if not folder_path:
        return HttpResponse(status=400)
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        coll_path = os.path.join(resource.resource_federation_path, res_id, folder_path)
    else:
        istorage = IrodsStorage()
        coll_path = os.path.join(res_id, folder_path)

    try:
        istorage.session.run("imkdir", None, '-p', coll_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

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
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)

    folder_path = request.POST['folder_path']
    if folder_path is None:
        return HttpResponse(status=400)
    folder_path = str(folder_path).strip()
    if not folder_path:
        return HttpResponse(status=400)
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        coll_path = os.path.join(resource.resource_federation_path, res_id, folder_path)
    else:
        istorage = IrodsStorage()
        coll_path = os.path.join(res_id, folder_path)

    try:
        istorage.delete(coll_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

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
    res_id = request.POST['res_id']
    if res_id is None:
        return HttpResponse(status=400)
    res_id = str(res_id).strip()
    try:
        resource, _, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    except (NotFound, PermissionDenied):
        # return permission defined response
        return HttpResponse(status=403)

    src_path = request.POST['source_path']
    tgt_path = request.POST['target_path']
    if src_path is None or tgt_path is None:
        return HttpResponse(status=400)
    src_path = str(src_path).strip()
    tgt_path = str(tgt_path).strip()
    if not src_path or not tgt_path:
        return HttpResponse(status=400)
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        src_full_path = os.path.join(resource.resource_federation_path, res_id, src_path)
        tgt_full_path = os.path.join(resource.resource_federation_path, res_id, tgt_path)
    else:
        istorage = IrodsStorage()
        src_full_path = os.path.join(res_id, src_path)
        tgt_full_path = os.path.join(res_id, tgt_path)

    tgt_file_name = os.path.basename(tgt_full_path)
    src_file_name = os.path.basename(src_full_path)

    # ensure the target_full_path contains the file name to be moved or renamed to
    if tgt_file_name != src_file_name:
        tgt_full_path = os.path.join(tgt_full_path, src_file_name)

    try:
        istorage.moveFile(src_full_path, tgt_full_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    rename_irods_file_in_django(resource, src_full_path, tgt_full_path)

    return_object = {'target_rel_path': tgt_path}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )
