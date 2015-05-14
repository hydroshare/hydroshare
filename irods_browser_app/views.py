import json
import os
from django.http import HttpResponse, HttpResponseRedirect
from irods.session import iRODSSession
from irods.exception import CollectionDoesNotExist
from hs_core import hydroshare

irods_sess = None

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
        user = str(request.POST['user'])
        password = str(request.POST['password'])
        zone = str(request.POST['zone'])
        host = str(request.POST['host'])
        datastore = "/%s/home/%s" % (zone, user)

        response_data = {}

        global irods_sess
        irods_sess = iRODSSession(user=user, password=password, zone=zone, host=host, port=port)

        try:
            irods_sess.collections.get(datastore)
        except CollectionDoesNotExist:
            request.session['irods_loggedin'] = False
            request.session['login_message'] = 'iRODS login failed'
            request.session['irods_file_name'] = ''
            response_data['irods_loggedin'] = False
            response_data['login_message'] = 'iRODS login failed'
            response_data['irods_file_name'] = ''
            response_data['error'] = "iRODS collection does not exist"
            return HttpResponse(
                json.dumps(response_data),
                content_type="application/json"
            )
        else:
            request.session["user"] = user
            request.session["datastore"] = datastore
            request.session["password"] = password
            request.session["port"] = port
            request.session["host"] = host
            request.session["zone"] = zone
            request.session['irods_loggedin'] = True
            request.session['irods_file_name'] = ''

            response_data['user'] = user
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
    return_object = []
    global irods_sess
    if not irods_sess:
        irods_sess = iRODSSession(user=request.session.get('user'), password=request.session.get('password'),
                                  zone=request.session.get('zone'), host=request.session.get('host'),
                                  port=request.session.get('port'))
    coll = irods_sess.collections.get(str(request.POST['store']))
    store = search_ds(coll)
    return_object.append(store['files'])
    return_object.append(store['folder'])
    return HttpResponse(json.dumps(return_object), status=201)

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
        request.session['irods_loggedin'] = True
        # create resource using irods file
        request.session['irods_file_name'] = file_name
        response_data['irods_file_name'] = file_name
        if valid:
            response_data['file_type_error'] = ''
        else:
            response_data['file_type_error'] = "Invalid file type: {ext}".format(ext=ext)

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
    file_name = str(request.POST['upload'])
    request.session['irods_loggedin'] = True
    # add irods file into an existing resource
    request.session['irods_add_file_name'] = file_name
    res_id = request.POST['res_id']
    return HttpResponseRedirect('/hsapi/_internal/{res_id}/add-file-to-resource/'.format(res_id=res_id))