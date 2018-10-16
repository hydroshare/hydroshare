import datetime
import json
import mimetypes
import os
import random
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
from rest_framework.decorators import api_view

from django_irods import icommands
from django_irods.storage import IrodsStorage
from hs_core.hydroshare import check_resource_type
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.hydroshare.resource import FILE_SIZE_LIMIT
from hs_core.signals import pre_download_file, pre_check_bag_flag
from hs_core.tasks import create_bag_by_irods, create_temp_zip, delete_zip
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from . import models as m
from .icommands import Session, GLOBAL_SESSION
from hs_core.models import ResourceFile


def download(request, path, rest_call=False, use_async=True, use_reverse_proxy=True,
             *args, **kwargs):
    split_path_strs = path.split('/')
    is_bag_download = False
    is_zip_download = False
    is_sf_agg_file = False
    if split_path_strs[0] == 'bags':
        res_id = os.path.splitext(split_path_strs[1])[0]
        is_bag_download = True
    elif split_path_strs[0] == 'zips':
        if path.endswith('.zip'):
            res_id = os.path.splitext(split_path_strs[2])[0]
        else:
            res_id = os.path.splitext(split_path_strs[1])[0]
        is_zip_download = True
    else:
        res_id = split_path_strs[0]

    # if the resource does not exist in django, authorized will be false
    res, authorized, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                   raises_exception=False)
    if not authorized:
        response = HttpResponse(status=401)
        content_msg = "You do not have permission to download this resource!"
        if rest_call:
            raise PermissionDenied(content_msg)
        else:
            response.content = "<h1>" + content_msg + "</h1>"
            return response

    if res.resource_type == "CompositeResource" and not path.endswith(".zip"):
        for f in ResourceFile.objects.filter(object_id=res.id):
            if path == f.storage_path:
                if f.has_logical_file and f.logical_file.is_single_file_aggregation:
                    is_sf_agg_file = True

    if res.resource_federation_path:
        # the resource is stored in federated zone
        istorage = IrodsStorage('federated')
        federated_path = res.resource_federation_path
        path = os.path.join(federated_path, path)
        session = icommands.ACTIVE_SESSION
    else:
        # TODO: From Alva: I do not understand the use case for changing the environment.
        # TODO: This seems an enormous potential vulnerability, as arguments are
        # TODO: passed from the URI directly to IRODS without verification.
        istorage = IrodsStorage()
        federated_path = ''
        if 'environment' in kwargs:
            environment = int(kwargs['environment'])
            environment = m.RodsEnvironment.objects.get(pk=environment)
            session = Session("/tmp/django_irods", settings.IRODS_ICOMMANDS_PATH,
                              session_id=uuid4())
            session.create_environment(environment)
            session.run('iinit', None, environment.auth)
        elif getattr(settings, 'IRODS_GLOBAL_SESSION', False):
            session = GLOBAL_SESSION
        elif icommands.ACTIVE_SESSION:
            session = icommands.ACTIVE_SESSION
        else:
            raise KeyError('settings must have IRODS_GLOBAL_SESSION set '
                           'if there is no environment object')

    resource_cls = check_resource_type(res.resource_type)

    if federated_path:
        res_root = os.path.join(federated_path, res_id)
    else:
        res_root = res_id

    if is_zip_download or is_sf_agg_file:
        if not path.endswith(".zip"):  # requesting folder that needs to be zipped
            input_path = path.split(res_id)[1]
            random_hash = random.getrandbits(32)
            daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
            random_hash_path = 'zips/{daily_date}/{res_id}/{rand_folder}'.format(
                daily_date=daily_date, res_id=res_id,
                rand_folder=random_hash)
            output_path = '{random_hash_path}{path}.zip'.format(random_hash_path=random_hash_path,
                                                                path=input_path)

            if res.resource_type == "CompositeResource":
                aggregation_name = input_path[len('/data/contents/'):]
                res.create_aggregation_xml_documents(aggregation_name=aggregation_name)

            if use_async:
                task = create_temp_zip.apply_async((res_id, input_path, output_path,
                                                    is_sf_agg_file), countdown=3)
                delete_zip.apply_async((random_hash_path, ),
                                       countdown=(20 * 60))  # delete after 20 minutes
                if is_sf_agg_file:
                    download_path = request.path.split(res_id)[0] + output_path
                else:
                    download_path = request.path.split("zips")[0] + output_path
                if rest_call:
                    return HttpResponse(json.dumps({'zip_status': 'Not ready',
                                                    'task_id': task.task_id,
                                                    'download_path': download_path}),
                                        content_type="application/json")
                request.session['task_id'] = task.task_id
                request.session['download_path'] = download_path
                return HttpResponseRedirect(res.get_absolute_url())

            ret_status = create_temp_zip(res_id, input_path, output_path, is_sf_agg_file)
            delete_zip.apply_async((random_hash_path, ),
                                   countdown=(20 * 60))  # delete after 20 minutes
            if not ret_status:
                content_msg = "Zip cannot be created successfully. Check log for details."
                response = HttpResponse()
                if rest_call:
                    response.content = content_msg
                else:
                    response.content = "<h1>" + content_msg + "</h1>"
                return response

            path = output_path

    bag_modified = istorage.getAVU(res_root, 'bag_modified')
    # make sure if bag_modified is not set to true, we still recreate the bag if the
    # bag file does not exist for some reason to resolve the error to download a nonexistent
    # bag when bag_modified is false due to the flag being out-of-sync with the real bag status
    if bag_modified is None or bag_modified.lower() == "false":
        # check whether the bag file exists
        bag_file_name = res_id + '.zip'
        if res_root.startswith(res_id):
            bag_full_path = os.path.join('bags', bag_file_name)
        else:
            bag_full_path = os.path.join(federated_path, 'bags', bag_file_name)
        # set bag_modified to 'true' if the bag does not exist so that it can be recreated
        # and the bag_modified AVU will be set correctly as well subsequently
        if not istorage.exists(bag_full_path):
            bag_modified = 'true'

    metadata_dirty = istorage.getAVU(res_root, 'metadata_dirty')
    # do on-demand bag creation
    # needs to check whether res_id collection exists before getting/setting AVU on it
    # to accommodate the case where the very same resource gets deleted by another request
    # when it is getting downloaded

    if is_bag_download:
        # send signal for pre_check_bag_flag
        pre_check_bag_flag.send(sender=resource_cls, resource=res)
        if bag_modified is None or bag_modified.lower() == "true":
            if metadata_dirty is None or metadata_dirty.lower() == 'true':
                create_bag_files(res)
            if use_async:
                # task parameter has to be passed in as a tuple or list, hence (res_id,) is needed
                # Note that since we are using JSON for task parameter serialization, no complex
                # object can be passed as parameters to a celery task
                task = create_bag_by_irods.apply_async((res_id,), countdown=3)
                if rest_call:
                    return HttpResponse(json.dumps({'bag_status': 'Not ready',
                                                    'task_id': task.task_id}),
                                        content_type="application/json")

                request.session['task_id'] = task.task_id
                request.session['download_path'] = request.path
                return HttpResponseRedirect(res.get_absolute_url())
            else:
                ret_status = create_bag_by_irods(res_id)
                if not ret_status:
                    content_msg = "Bag cannot be created successfully. Check log for details."
                    response = HttpResponse()
                    if rest_call:
                        response.content = content_msg
                    else:
                        response.content = "<h1>" + content_msg + "</h1>"
                    return response

    elif metadata_dirty is None or metadata_dirty.lower() == 'true':
        if path.endswith("resourcemap.xml") or path.endswith('resourcemetadata.xml'):
            # we need to regenerate the metadata xml files
            create_bag_files(res)

    # send signal for pre download file
    download_file_name = split_path_strs[-1]
    pre_download_file.send(sender=resource_cls, resource=res,
                           download_file_name=download_file_name,
                           request=request)

    # obtain mime_type to set content_type
    mtype = 'application-x/octet-stream'
    mime_type = mimetypes.guess_type(path)
    if mime_type[0] is not None:
        mtype = mime_type[0]
    # retrieve file size to set up Content-Length header
    stdout = session.run("ils", None, "-l", path)[0].split()
    flen = int(stdout[3])

    # If this path is resource_federation_path, then the file is a local user file
    userpath = '/' + os.path.join(
        getattr(settings, 'HS_USER_IRODS_ZONE', 'hydroshareuserZone'),
        'home',
        getattr(settings, 'HS_LOCAL_PROXY_USER_IN_FED_ZONE', 'localHydroProxy'))

    # Allow reverse proxy if request was forwarded by nginx
    # (HTTP_X_DJANGO_REVERSE_PROXY is 'true')
    # and reverse proxy is possible according to configuration.

    if use_reverse_proxy and getattr(settings, 'SENDFILE_ON', False) and \
       'HTTP_X_DJANGO_REVERSE_PROXY' in request.META:

        # The NGINX sendfile abstraction is invoked as follows:
        # 1. The request to download a file enters this routine via the /rest_download or /download
        #    url in ./urls.py. It is redirected here from Django. The URI contains either the
        #    unqualified resource path or the federated resource path, depending upon whether
        #    the request is local or federated.
        # 2. This deals with unfederated resources by redirecting them to the uri
        #    /irods-data/{resource-id}/... on nginx. This URI is configured to read the file
        #    directly from the iRODS vault via NFS, and does not work for direct access to the
        #    vault due to the 'internal;' declaration in NGINX.
        # 3. This deals with federated resources by reading their path, matching local vaults, and
        #    redirecting to URIs that are in turn mapped to read from appropriate iRODS vaults. At
        #    present, the only one of these is /irods-user, which handles files whose federation
        #    path is stored in the variable 'userpath'.
        # 4. If there is no vault available for the resource, the file is transferred without
        #    NGINX, exactly as it was transferred previously.

        # stop NGINX targets that are non-existent from hanging forever.
        if not istorage.exists(path):
            content_msg = "file path {} does not exist in iRODS".format(path)
            response = HttpResponse(status=404)
            if rest_call:
                response.content = content_msg
            else:
                response.content = "<h1>" + content_msg + "</h1>"
            return response

        if not res.is_federated:
            # invoke X-Accel-Redirect on physical vault file in nginx
            response = HttpResponse(content_type=mtype)
            response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
                name=path.split('/')[-1])
            response['Content-Length'] = flen
            response['X-Accel-Redirect'] = '/'.join([
                getattr(settings, 'IRODS_DATA_URI', '/irods-data'), path])
            return response

        elif res.resource_federation_path == userpath:  # this guarantees a "user" resource
            # invoke X-Accel-Redirect on physical vault file in nginx
            # if path is full user path; strip federation prefix
            if path.startswith(userpath):
                path = path[len(userpath)+1:]
            # invoke X-Accel-Redirect on physical vault file in nginx
            response = HttpResponse(content_type=mtype)
            response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
                name=path.split('/')[-1])
            response['Content-Length'] = flen
            response['X-Accel-Redirect'] = os.path.join(
                getattr(settings, 'IRODS_USER_URI', '/irods-user'), path)
            return response

    # if we get here, none of the above conditions are true
    if flen <= FILE_SIZE_LIMIT:
        options = ('-',)  # we're redirecting to stdout.
        # this unusual way of calling works for federated or local resources
        proc = session.run_safe('iget', None, path, *options)
        response = FileResponse(proc.stdout, content_type=mtype)
        response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
            name=path.split('/')[-1])
        response['Content-Length'] = flen
        return response

    else:
        content_msg = "File larger than 1GB cannot be downloaded directly via HTTP. " \
                      "Please download the large file via iRODS clients."
        response = HttpResponse(status=403)
        if rest_call:
            response.content = content_msg
        else:
            response.content = "<h1>" + content_msg + "</h1>"
        return response


@api_view(['GET'])
def rest_download(request, path, *args, **kwargs):
    # need to have a separate view function just for REST API call
    return download(request, path, rest_call=True, *args, **kwargs)


def check_task_status(request, task_id=None, *args, **kwargs):
    '''
    A view function to tell the client if the asynchronous create_bag_by_irods()
    task is done and the bag file is ready for download.
    Args:
        request: an ajax request to check for download status
    Returns:
        JSON response to return result from asynchronous task create_bag_by_irods
    '''
    if not task_id:
        task_id = request.POST.get('task_id')
    result = create_bag_by_irods.AsyncResult(task_id)
    if result.ready():
        return HttpResponse(json.dumps({"status": result.get()}),
                            content_type="application/json")
    else:
        return HttpResponse(json.dumps({"status": None}),
                            content_type="application/json")


@api_view(['GET'])
def rest_check_task_status(request, task_id, *args, **kwargs):
    # need to have a separate view function just for REST API call
    return check_task_status(request, task_id, *args, **kwargs)
