import json
import os
from django.http import HttpResponse, HttpResponseRedirect
from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist
from hs_core import hydroshare
from hs_core.views.utils import authorize, upload_from_irods
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
            response_data['irods_file_name'] = ''
            response_data['error'] = "iRODS collection does not exist"
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )
        else:
            response_data['user'] = user
            response_data['password'] = password
            response_data['port'] = port
            response_data['host'] = host
            response_data['zone'] = zone
            response_data['datastore'] = datastore
            response_data['irods_loggedin'] = True
            response_data['irods_file_name'] = ''
            return HttpResponse(
                json.dumps(response_data),
                content_type = "application/json"
            )
    else:
        return HttpResponse(
            json.dumps({"error": "Not POST request"}),
            content_type="application/json"
        )

def store(request):
    return_object = {}
    irods_sess = iRODSSession(user=str(request.POST['user']), password=str(request.POST['password']),
                                  zone=str(request.POST['zone']), host=str(request.POST['host']),
                                  port=int(request.POST['port']))
    datastore = str(request.POST['store'])
    coll = irods_sess.collections.get(datastore)
    store = search_ds(coll)

    return_object['files'] = store['files']
    return_object['folder'] = store['folder']

    return HttpResponse(
        json.dumps(return_object),
        content_type = "application/json"
    )

def upload(request):
    if request.method == 'POST':
        file_name = str(request.POST['upload'])

        resource_cls = hydroshare.check_resource_type(request.POST['res_type'])
        file_types = resource_cls.get_supported_upload_file_types()
        valid = False
        if file_types == ".*":
            valid = True
        else:
            ext = os.path.splitext(file_name)[1]
            if ext == file_types:
                valid = True
            else:
                for index in range(len(file_types)):
                    if ext == file_types[index].strip():
                        valid = True
                        break
        response_data = {}

        if valid:
            response_data['file_type_error'] = ''
            response_data['irods_file_name'] = file_name
        else:
            response_data['file_type_error'] = "Invalid file type: {ext}".format(ext=ext)
            response_data['irods_file_name'] = 'No file selected'

        return HttpResponse(
            json.dumps(response_data),
            content_type = "application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "Not POST request"}),
            content_type="application/json"
        )

def upload_add(request):
    # add irods file into an existing resource
    res_id = request.POST['res_id']
    resource, _, _ = authorize(request, res_id, edit=True, full=True, superuser=True)
    res_files = request.FILES.getlist('files')
    extract_metadata = request.REQUEST.get('extract-metadata', 'No')
    extract_metadata = True if extract_metadata.lower() == 'yes' else False

    irods_fname = request.POST.get('irods_file_name', '')
    res_cls = resource.__class__
    file_types = res_cls.get_supported_upload_file_types()
    valid = False
    if file_types == ".*":
        valid = True
    else:
        ext = os.path.splitext(irods_fname)[1]
        if ext == file_types:
            valid = True
        else:
            for index in range(len(file_types)):
                file_type_str = file_types[index].strip()
                if file_type_str == ".*" or ext == file_type_str:
                    valid = True
                    break

    if not valid:
        request.session['file_type_error'] = "Invalid file type: {ext}".format(ext=ext)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        user = request.POST.get('irods-username')
        password = request.POST.get("irods-password")
        port = request.POST.get("irods-port")
        host = request.POST.get("irods-host")
        zone = request.POST.get("irods-zone")
        try:
            upload_from_irods(username=user, password=password, host=host, port=port,
                              zone=zone, irods_fname=irods_fname, res_files=res_files)
        except Exception as ex:
            request.session['file_validation_error'] = ex.message
            return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        utils.resource_file_add_pre_process(resource=resource, files=res_files, user=request.user,
                                            extract_metadata=extract_metadata)

    except hydroshare.utils.ResourceFileSizeException as ex:
        request.session['file_size_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['file_validation_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files, user=request.user,
                                                   extract_metadata=extract_metadata)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['file_validation_error'] = ex.message

    return HttpResponseRedirect(request.META['HTTP_REFERER'])