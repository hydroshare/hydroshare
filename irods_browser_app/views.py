import os
from django.http import JsonResponse
from rest_framework import status

from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist


def search_ds(coll):
    store = {}
    file = []
    folder = []
    if coll.data_objects:
        for files in coll.data_objects:
            file.append(files.name)
    if coll.subcollections:
        for folders in coll.subcollections:
            folder.append(folders.name)

    store['files'] = file
    store['folder'] = folder
    return store


def check_upload_files(resource_cls, fnames_list):
    file_types = resource_cls.get_supported_upload_file_types()
    valid = False
    ext = ''
    if file_types == ".*":
        valid = True
    else:
        for fname in fnames_list:
            ext = os.path.splitext(fname)[1].lower()
            if ext == file_types:
                valid = True
            else:
                for index in range(len(file_types)):
                    file_type_str = file_types[index].strip().lower()
                    if file_type_str == ".*" or ext == file_type_str:
                        valid = True
                        break

    return (valid, ext)


# Create your views here.
def login(request):
    if request.method == 'POST':
        port = int(request.POST['port'])
        user = str(request.POST['username'])
        password = str(request.POST['password'])
        zone = str(request.POST['zone'])
        host = str(request.POST['host'])
        datastore = "/%s/home/%s" % (zone, user)

        response_data = {}

        irods_sess = iRODSSession(user=user, password=password, zone=zone, host=host, port=port)

        try:
            irods_sess.collections.get(datastore)
        except CollectionDoesNotExist:
            response_data['irods_loggedin'] = False
            response_data['login_message'] = 'iRODS login failed'
            response_data['error'] = "iRODS collection does not exist"
            irods_sess.cleanup()
            return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_data['user'] = user
            response_data['password'] = password
            response_data['port'] = port
            response_data['host'] = host
            response_data['zone'] = zone
            response_data['datastore'] = datastore
            response_data['irods_loggedin'] = True
            irods_sess.cleanup()
            return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        return JsonResponse({"error": "Not POST request"}, status=status.HTTP_400_BAD_REQUEST)


def store(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in an iRODS zone the requested user has logged in.
    It is invoked by an AJAX call, so it returns json object that holds content for files and folders
    under the requested directory/collection/subcollection
    """
    return_object = {}
    irods_sess = iRODSSession(user=str(request.POST['user']), password=str(request.POST['password']),
                              zone=str(request.POST['zone']), host=str(request.POST['host']),
                              port=int(request.POST['port']))
    datastore = str(request.POST['store'])
    coll = irods_sess.collections.get(datastore)
    store = search_ds(coll)

    return_object['files'] = store['files']
    return_object['folder'] = store['folder']
    irods_sess.cleanup()
    return JsonResponse(return_object, status=status.HTTP_200_OK)
