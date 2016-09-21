import json
import logging
import os

from django.http import HttpResponse
from rest_framework.exceptions import NotFound, PermissionDenied

from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_file_mime_type
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import delete_resource_file
from hs_core.models import ResourceFile

logger = logging.getLogger(__name__)

def link_irods_file_to_django(resource, filename, size=0):
    # link the newly created zip file to Django resource model
    if resource:
        if resource.resource_federation_path:
            ResourceFile.objects.create(content_object=resource,
                                        resource_file=None,
                                        fed_resource_file_name_or_path=filename,
                                        fed_resource_file_size=size)
        else:
            ResourceFile.objects.create(content_object=resource,
                                        resource_file=filename)

def link_irods_folder_to_django(resource, istorage, foldername, exclude=()):
    if resource and istorage and foldername:
        store = istorage.listdir(foldername)
        # add the unzipped files into Django resource model
        for file in store[1]:
            if not file in exclude:
                file_path = os.path.join(foldername, file)
                size = istorage.size(file_path)
                link_irods_file_to_django(resource, file_path, size)
        for folder in store[0]:
            link_irods_folder_to_django(resource, istorage, os.path.join(foldername, folder), exclude)

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
            files.append({'name': fname, 'size': size, 'type': mtype})
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    return_object = {'files': files,
                     'folders': store[0]}

    return HttpResponse(
        json.dumps(return_object),
        content_type = "application/json"
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

    content_dir = res_coll_input
    output_zip_full_path = os.path.join(content_dir, output_zip_fname)
    try:
        if bool_remove_original:
            store = istorage.listdir(res_coll_input)
        istorage.session.run("ibun", None, '-cDzip', '-f', output_zip_full_path, res_coll_input)
        size = istorage.size(output_zip_full_path)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    link_irods_file_to_django(resource, output_zip_full_path, size)

    if bool_remove_original:
        try:
            for folder in store[0]:
                delete_resource_file(res_id, folder, request.user)
            for file in store[1]:
                delete_resource_file(res_id, file, request.user)
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

    coll_dir = os.path.dirname(zip_with_full_path)
    # has to go above one directory as the collection path to unzip file to
    coll_dir = os.path.dirname(coll_dir)
    unzip_path = os.path.dirname(zip_with_full_path)
    zip_fname = os.path.basename(zip_with_rel_path)
    try:
        istorage.session.run("ibun", None, '-xfDzip', zip_with_full_path, coll_dir)
        link_irods_folder_to_django(resource, istorage, unzip_path, (zip_fname))
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
