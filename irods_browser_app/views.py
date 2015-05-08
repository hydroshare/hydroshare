import json
from django.http import HttpResponse, HttpResponseRedirect
from irods.session import iRODSSession

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
        irods_sess.collections.get(datastore)
    except:
        request.session['irods_loggedin'] = False
        request.session['login_message'] = 'iRODS login failed'
        request.session['irods_file_name'] = ''
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
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
        request.session['irods_loggedin'] = True
        request.session['irods_file_name'] = ''
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

def store(request):
    return_object = []
    global irods_sess
    coll = irods_sess.collections.get(str(request.POST['store']))
    store = search_ds(coll)
    return_object.append(store['files'])
    return_object.append(store['folder'])
    return HttpResponse(json.dumps(return_object), status=201)

def upload(request):
    file_name = str(request.POST['upload'])
    request.session['irods_loggedin'] = True
    request.session['irods_file_name'] = file_name
    return HttpResponseRedirect(request.META['HTTP_REFERER'])