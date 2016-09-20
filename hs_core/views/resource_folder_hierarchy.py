import json
import logging

from django.http import HttpResponse

from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_file_mime_type

logger = logging.getLogger(__name__)

def data_store_structure(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in hydroshareZone or any federated zone used for HydroShare resource backend store.
    It is invoked by an AJAX call, so it returns json object that holds content for files
    and folders under the requested directory/collection/subcollection.
    The AJAX request must be a POST request with input data passed in for res_id and store_path
    where store_path is the relative path under res_id collection/directory
    """
    res_id = str(request.POST['res_id']).strip()
    if res_id is None:
        return HttpResponse(status=400)
    resource = get_resource_by_shortkey(res_id)
    store_path = str(request.POST['store_path']).strip()
    # store_path is support to be relative path, so strip the first / if any
    if store_path:
        if store_path[0]=='/':
            store_path = store_path[1:]
    else:
        return HttpResponse(status=400)

    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_coll = '{}/{}/{}'.format(resource.resource_federation_path, res_id, store_path)
    else:
        istorage = IrodsStorage()
        res_coll = '{}/{}'.format(res_id, store_path)

    try:
        store = istorage.listdir(res_coll)
        files = []
        for fname in store[1]:
            name_with_full_path = '{}/{}'.format(res_coll, fname)
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
    used for HydroShare resource backend store. It is invoked by an AJAX call, so it returns
    json object that holds the created zip file name if it succeeds, and an empty string
    if it fails. The AJAX request must be a POST request with input data passed in for
    res_id, input_coll_path, output_zip_file_name, and remove_original_after_zip where
    input_coll_path is the relative sub-collection path under res_id collection to be zipped,
    output_zip_file_name is the file name only with no path of the generated zip file name,
    and remove_original_after_zip has a value of "true" or "false" (default is "true") indicating
    whether original files will be deleted after zipping.
    """
    res_id = str(request.POST['res_id'])
    if res_id is None:
        return HttpResponse(status=400)
    resource = get_resource_by_shortkey(res_id)
    input_coll_path = str(request.POST['input_coll_path']).strip()
    # input_coll_path is support to be relative path, so strip the first / if any
    if input_coll_path is None:
        return HttpResponse(status=400)
    if input_coll_path[0]=='/':
        input_coll_path = input_coll_path[1:]
    output_zip_fname = str(request.POST['output_zip_file_name']).strip()
    if output_zip_fname is None:
        return HttpResponse(status=400)
    remove_original = str(request.POST['remove_original_after_zip']).strip()
    bool_remove_original = True
    if remove_original:
        remove_original = remove_original.lower()
        if remove_original == 'false':
            bool_remove_original = False

    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_coll_input = '{}/{}/{}'.format(resource.resource_federation_path, res_id,
                                           input_coll_path)
        content_dir = '{}/{}/data/contents'.format(resource.resource_federation_path, res_id)
    else:
        istorage = IrodsStorage()
        res_coll_input = '{}/{}'.format(res_id, input_coll_path)
        content_dir = '{}/data/contents'.format(res_id)
    output_zip_full_path = '{}/{}'.format(content_dir, output_zip_fname)
    try:
        istorage.session.run("ibun", None, '-cDzip', '-f', output_zip_full_path, res_coll_input)
        size = istorage.size(output_zip_full_path)
        if bool_remove_original:
            istorage.delete(res_coll_input)
    except SessionException as ex:
        logger.error(ex.stderr)
        return HttpResponse(status=500)

    return_object = {'name': output_zip_fname,
                     'size': size,
                     'type': 'zip'}

    return HttpResponse(
        json.dumps(return_object),
        content_type="application/json"
    )
