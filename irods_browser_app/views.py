import json
import os
import string
from django.http import JsonResponse
from rest_framework import status

from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist

from django_irods.icommands import SessionException
from hs_core import hydroshare
from hs_core.views.utils import authorize, upload_from_irods, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import utils


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


def upload_add(request):
    # add irods file into an existing resource
    res_id = request.POST.get('res_id', '')
    resource, _, _ = authorize(request, res_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res_files = request.FILES.getlist('files')
    extract_metadata = request.POST.get('extract-metadata', 'No')
    extract_metadata = True if extract_metadata.lower() == 'yes' else False
    irods_fnames = request.POST.get('upload', '')
    irods_fnames_list = string.split(irods_fnames, ',')
    res_cls = resource.__class__

    # TODO: read resource type from resource, not from input file 
    valid, ext = check_upload_files(res_cls, irods_fnames_list)
    source_names = []
    if not valid:
        return JsonResponse({'error': "Invalid file type: {ext}".format(ext=ext)},
                            status=status.HTTP_400_BAD_REQUEST)
    else:
        homepath = irods_fnames_list[0]
        # TODO: this should happen whether resource is federated or not
        irods_federated = utils.is_federated(homepath)
        if irods_federated:
            source_names = irods_fnames.split(',')
        else:
            user = request.POST.get('irods_username')
            password = request.POST.get("irods_password")
            port = request.POST.get("irods_port")
            host = request.POST.get("irods_host")
            zone = request.POST.get("irods_zone")
            try:
                upload_from_irods(username=user, password=password, host=host, port=port,
                                  zone=zone, irods_fnames=irods_fnames, res_files=res_files)
            except SessionException as ex:
                return JsonResponse(
                    {"error": ex.stderr}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

    try:
        utils.resource_file_add_pre_process(resource=resource, files=res_files, user=request.user,
                                            extract_metadata=extract_metadata, 
                                            source_names=source_names, folder=None)
    except hydroshare.utils.ResourceFileSizeException as ex:
        return JsonResponse({'error': ex.message}, status=status.HTTP_400_BAD_REQUEST)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        return JsonResponse({'error': ex.message}, status=status.HTTP_400_BAD_REQUEST)

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files, 
                                                   user=request.user,
                                                   extract_metadata=extract_metadata,
                                                   source_names=source_names, folder=None)

    except (hydroshare.utils.ResourceFileValidationException, SessionException) as ex:
        if ex.message:
            return JsonResponse({'error': ex.message},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        elif ex.stderr:
            return JsonResponse({'error': ex.stderr},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return JsonResponse({}, status=status.HTTP_200_OK)
