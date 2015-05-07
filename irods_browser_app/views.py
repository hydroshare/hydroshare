import json
from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from irods.session import iRODSSession

irods_sess = None

def search_ds(coll):
    print coll
    store = {}
    file = []
    folder = []
    if (coll.data_objects != []):
        for files in coll.data_objects:
            file.append(files.name)
    if (coll.subcollections != []):
        for folders in coll.subcollections:
            folder.append(folders.name)

    store['files'] = file
    store['folder'] = folder
    return store

# Create your views here.
def login(request):
    port = int(request.POST['port'])
    user = str(request.POST['username'])
    password = str(request.POST['password'])
    zone = str(request.POST['zone'])
    host = str(request.POST['host'])
    datastore = "/%s/home/%s" % (zone, user)
    remember = request.POST.get('remember', None)
    global irods_sess
    irods_sess = iRODSSession(user=user, password=password, zone=zone, host=host, port=port)

    try:
        irods_coll = irods_sess.collections.get(datastore)
    except:
        context = {
            'irods_loggedin': False,
            'login_message': 'iRODS login failed'
        }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))
    else:
        request.session["user"] = user
        request.session["datastore"] = datastore
        request.session["password"] = password
        request.session["port"] = port
        request.session["host"] = host
        request.session["zone"] = zone
        if remember:
            request.session["remember"] = remember
        else:
            request.session["remember"] = ''
        context = {
            'irods_loggedin': True,
            'irods_user': user,
            'irods_file_name': 'No file selected'
        }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))


def store(request):
    return_object = []
    user = request.session["user"]
    password = request.session["password"]
    port = request.session["port"]
    host = request.session["host"]
    zone = request.session["zone"]

    global irods_sess
    coll = irods_sess.collections.get(str(request.POST['store']))
    store = search_ds(coll)
    return_object.append(store['files'])
    return_object.append(store['folder'])

    return HttpResponse(json.dumps(return_object), status=201)

def upload(request):
    global work_space
    if request.method == 'POST':
        file_name = str(request.POST['upload'])
        user = request.session["user"]

        context = {
            'irods_loggedin': True,
            'irods_user': user,
            'irods_file_name': file_name,
        }
        return render_to_response('pages/create-resource.html', context, context_instance=RequestContext(request))