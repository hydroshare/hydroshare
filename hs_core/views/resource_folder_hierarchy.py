import json
from django.http import HttpResponse

from django_irods.storage import IrodsStorage
from hs_core.hydroshare.utils import get_resource_by_shortkey, get_file_mime_type

def data_store_structure(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in an iRODS zone the requested user has logged in.
    It is invoked by an AJAX call, so it returns json object that holds content for files
    and folders under the requested directory/collection/subcollection.
    The AJAX request must be a POST request with input data passed in for res_id and store_path
    where store_path is the relative path under res_id collection/directory
    """
    res_id = str(request.POST['res_id'])
    store_path = str(request.POST['store_path']).strip()
    # store_path is support to be relative path, so strip the first / if any
    if store_path:
        if store_path[0]=='/':
            store_path = store_path[1:]

    resource = get_resource_by_shortkey(res_id)
    return_object = {}
    if resource.resource_federation_path:
        istorage = IrodsStorage('federated')
        res_coll = '{}/{}/{}'.format(resource.resource_federation_path,
                                        res_id, store_path)
    else:
        istorage = IrodsStorage()
        res_coll = '{}/{}'.format(res_id, store_path)

    store = istorage.listdir(res_coll)

    files = []
    for fname in store[1]:
        name_with_full_path = '{}/{}'.format(res_coll, fname)
        size = istorage.size(name_with_full_path)
        type = get_file_mime_type(fname)
        idx = type.find('/')
        if idx >= 0:
            type = type[idx+1:]
        files.append({'name': fname, 'size': size, 'type': type})

    return_object['files'] = files
    return_object['folders'] = store[0]

    jsondump = json.dumps(return_object)
    return HttpResponse(
        jsondump,
        content_type = "application/json"
    )
