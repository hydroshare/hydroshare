import datetime
import json
import mimetypes
import os
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
from rest_framework.decorators import api_view

from django_irods import icommands
from hs_core.hydroshare import check_resource_type
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.signals import pre_download_file, pre_check_bag_flag
from hs_core.tasks import create_bag_by_irods, create_temp_zip, delete_zip
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from . import models as m
from .icommands import Session, GLOBAL_SESSION
from hs_core.models import ResourceFile

import logging
logger = logging.getLogger(__name__)


def download(request, path, rest_call=False, use_async=True, use_reverse_proxy=True,
             *args, **kwargs):
    """ perform a download request, either asynchronously or synchronously

    :param request: the request object.
    :param path: the path of the thing to be downloaded.
    :param rest_call: True if calling from REST API
    :param use_async: True means to utilize asynchronous creation of objects to download.
    :param use_reverse_proxy: True means to utilize NGINX reverse proxy for streaming.

    The following variables are computed:

    * `path` is the public path of the thing to be downloaded.
    * `irods_path` is the location of `path` in irods.
    * `output_path` is the output path to be reported in the response object.
    * `irods_output_path` is the location of `output_path` in irods

    and there are six cases:

    Zipped query param signal the download should be zipped
        - folders are always zipped regardless of this paramter
        - single file aggregations are zipped with the aggregation metadata files

    A path may point to:
    1. a single file
    2. a single-file-aggregation object in a composite resource.
    3. a folder
    3. a metadata object that may need updating.
    4. a bag that needs to be updated and then returned.
    6. a previously zipped file that was zipped asynchronously.

    """
    if __debug__:
        logger.debug("request path is {}".format(path))

    split_path_strs = path.split('/')
    while split_path_strs[-1] == '':
        split_path_strs.pop()
    path = u'/'.join(split_path_strs)  # no trailing slash

    # initialize case variables
    is_bag_download = False
    is_zip_download = False
    is_zip_request = request.GET.get('zipped', "False").lower() == "true"
    is_sf_agg_file = False
    is_sf_request = False

    if split_path_strs[0] == 'bags':
        is_bag_download = True
        # format is bags/{rid}.zip
        res_id = os.path.splitext(split_path_strs[1])[0]
    elif split_path_strs[0] == 'zips':
        is_zip_download = True
        # zips prefix means that we are following up on an asynchronous download request
        # format is zips/{date}/{zip-uuid}/{public-path}.zip where {public-path} contains the rid
        res_id = split_path_strs[3]
    else:  # regular download request
        res_id = split_path_strs[0]

    if __debug__:
        logger.debug("resource id is {}".format(res_id))

    # now we have the resource Id and can authorize the request
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

    # default values are changed later as needed

    istorage = res.get_irods_storage()
    if res.is_federated:
        irods_path = os.path.join(res.resource_federation_path, path)
    else:
        irods_path = path
    # in many cases, path and output_path are the same.
    output_path = path

    irods_output_path = irods_path
    # folder requests are automatically zipped
    if not is_bag_download and not is_zip_download:  # path points into resource: should I zip it?
        store_path = u'/'.join(split_path_strs[1:])  # data/contents/{path-to-something}
        if res.is_folder(store_path):  # automatically zip folders
            is_zip_request = True
            daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
            output_path = "zips/{}/{}/{}.zip".format(daily_date, uuid4().hex, path)
            if res.is_federated:
                irods_output_path = os.path.join(res.resource_federation_path, output_path)
            else:
                irods_output_path = output_path
            if __debug__:
                logger.debug("automatically zipping folder {} to {}".format(path, output_path))
        elif istorage.exists(irods_path):
            if __debug__:
                logger.debug("request for single file {}".format(path))
            is_sf_request = True

            # check for single file aggregations
            if "data/contents/" in path:  # not a metadata file
                for f in ResourceFile.objects.filter(object_id=res.id):
                    if path == f.storage_path:
                        is_sf_agg_file = True
                        if not is_zip_request and f.has_logical_file and \
                                f.logical_file.is_single_file_aggregation:
                            download_url = request.GET.get('url_download', 'false').lower()
                            if download_url == 'false':
                                # redirect to referenced url in the url file instead
                                redirect_url = f.logical_file.redirect_url
                                if redirect_url:
                                    return HttpResponseRedirect(redirect_url)
                        if __debug__:
                            logger.debug(
                                "request for single file aggregation {}".format(path))
                        break

            if is_zip_request:
                daily_date = datetime.datetime.today().strftime('%Y-%m-%d')
                output_path = "zips/{}/{}/{}.zip".format(daily_date, uuid4().hex, path)
                if res.is_federated:
                    irods_output_path = os.path.join(res.resource_federation_path, output_path)
                else:
                    irods_output_path = output_path

    # After this point, we have valid path, irods_path, output_path, and irods_output_path
    # * is_zip_request: signals download should be zipped, folders are always zipped
    # * is_sf_agg_file: path is a single-file aggregation in Composite Resource
    # * is_sf_request: path is a single-file
    # flags for download:
    # * is_bag_download: download a bag in format bags/{rid}.zip
    # * is_zip_download: download a zipfile in format zips/{date}/{random guid}/{path}.zip
    # if none of these are set, it's a normal download

    # determine active session
    if res.is_federated:
        # the resource is stored in federated zone
        session = icommands.ACTIVE_SESSION
    else:
        # TODO: From Alva: I do not understand the use case for changing the environment.
        # TODO: This seems an enormous potential vulnerability, as arguments are
        # TODO: passed from the URI directly to IRODS without verification.
        if 'environment' in kwargs:
            logger.warn("setting iRODS from environment")
            environment = int(kwargs['environment'])
            environment = m.RodsEnvironment.objects.get(pk=environment)
            session = Session("/tmp/django_irods", settings.IRODS_ICOMMANDS_PATH,
                              session_id=uuid4())
            session.create_environment(environment)
            session.run('iinit', None, environment.auth)
        elif getattr(settings, 'IRODS_GLOBAL_SESSION', False):
            if __debug__:
                logger.debug("using GLOBAL_SESSION")
            session = GLOBAL_SESSION
        elif icommands.ACTIVE_SESSION:
            if __debug__:
                logger.debug("using ACTIVE_SESSION")
            session = icommands.ACTIVE_SESSION
        else:
            raise KeyError('settings must have IRODS_GLOBAL_SESSION set '
                           'if there is no environment object')

    resource_cls = check_resource_type(res.resource_type)

    if is_zip_request:

        if use_async:
            task = create_temp_zip.apply_async((res_id, irods_path, irods_output_path,
                                                is_sf_agg_file, is_sf_request))
            delete_zip.apply_async((irods_output_path, ),
                                   countdown=(60 * 60 * 24))  # delete after 24 hours

            if rest_call:
                return HttpResponse(
                    json.dumps({
                        'zip_status': 'Not ready',
                        'task_id': task.task_id,
                        'download_path': '/django_irods/rest_download/' + output_path}),
                    content_type="application/json")
            else:
                # return status to the UI
                request.session['task_id'] = task.task_id
                # TODO: this is mistaken for a bag download in the UI!
                # TODO: multiple asynchronous downloads don't stack!
                request.session['download_path'] = '/django_irods/download/' + output_path
                # redirect to resource landing page, which interprets session variables.
                return HttpResponseRedirect(res.get_absolute_url())

        else:  # synchronous creation of download
            ret_status = create_temp_zip(res_id, irods_path, irods_output_path,
                                         is_sf_agg_file, is_sf_request)
            delete_zip.apply_async((irods_output_path, ),
                                   countdown=(60 * 60 * 24))  # delete after 24 hours
            if not ret_status:
                content_msg = "Zip could not be created."
                response = HttpResponse()
                if rest_call:
                    response.content = content_msg
                else:
                    response.content = "<h1>" + content_msg + "</h1>"
                return response
            # At this point, output_path presumably exists and contains a zipfile
            # to be streamed below

    elif is_bag_download:
        # Shorten request if it contains extra junk at the end
        bag_file_name = res_id + '.zip'
        output_path = os.path.join('bags', bag_file_name)
        if not res.is_federated:
            irods_output_path = output_path
        else:
            irods_output_path = os.path.join(res.resource_federation_path, output_path)

        bag_modified = res.getAVU('bag_modified')
        # recreate the bag if it doesn't exist even if bag_modified is "false".
        if __debug__:
            logger.debug(u"irods_output_path is {}".format(irods_output_path))
        if bag_modified is None or not bag_modified:
            if not istorage.exists(irods_output_path):
                bag_modified = True

        # send signal for pre_check_bag_flag
        # this generates metadata other than that generated by create_bag_files.
        pre_check_bag_flag.send(sender=resource_cls, resource=res)

        metadata_dirty = res.getAVU('metadata_dirty')
        if metadata_dirty is None or metadata_dirty:
            create_bag_files(res)  # sets metadata_dirty to False
            bag_modified = "True"

        if bag_modified is None or bag_modified:
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

    else:  # regular file download
        # if fetching main metadata files, then these need to be refreshed.
        if path.endswith("resourcemap.xml") or path.endswith('resourcemetadata.xml'):
            metadata_dirty = res.getAVU("metadata_dirty")
            if metadata_dirty is None or metadata_dirty:
                create_bag_files(res)  # sets metadata_dirty to False

        # send signal for pre download file
        # TODO: does not contain subdirectory information: duplicate refreshes possible
        download_file_name = split_path_strs[-1]  # end of path
        # this logs the download request in the tracking system
        pre_download_file.send(sender=resource_cls, resource=res,
                               download_file_name=download_file_name,
                               request=request)

    # If we get this far,
    # * path and irods_path point to true input
    # * output_path and irods_output_path point to true output.
    # Try to stream the file back to the requester.

    # obtain mime_type to set content_type
    mtype = 'application-x/octet-stream'
    mime_type = mimetypes.guess_type(output_path)
    if mime_type[0] is not None:
        mtype = mime_type[0]
    # retrieve file size to set up Content-Length header
    # TODO: standardize this to make it less brittle
    stdout = session.run("ils", None, "-l", irods_output_path)[0].split()
    flen = int(stdout[3])

    # Allow reverse proxy if request was forwarded by nginx (HTTP_X_DJANGO_REVERSE_PROXY='true')
    # and reverse proxy is possible according to configuration (SENDFILE_ON=True)
    # and reverse proxy isn't overridden by user (use_reverse_proxy=True).

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

        # If this path is resource_federation_path, then the file is a local user file
        userpath = '/' + os.path.join(
            getattr(settings, 'HS_USER_IRODS_ZONE', 'hydroshareuserZone'),
            'home',
            getattr(settings, 'HS_LOCAL_PROXY_USER_IN_FED_ZONE', 'localHydroProxy'))

        # stop NGINX targets that are non-existent from hanging forever.
        if not istorage.exists(irods_output_path):
            content_msg = "file path {} does not exist in iRODS".format(output_path)
            response = HttpResponse(status=404)
            if rest_call:
                response.content = content_msg
            else:
                response.content = "<h1>" + content_msg + "</h1>"
            return response

        if not res.is_federated:
            # track download count
            res.update_download_count()

            # invoke X-Accel-Redirect on physical vault file in nginx
            response = HttpResponse(content_type=mtype)
            response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
                name=output_path.split('/')[-1])
            response['Content-Length'] = flen
            response['X-Accel-Redirect'] = '/'.join([
                getattr(settings, 'IRODS_DATA_URI', '/irods-data'), output_path])
            if __debug__:
                logger.debug("Reverse proxying local {}".format(response['X-Accel-Redirect']))
            return response

        elif res.resource_federation_path == userpath:  # this guarantees a "user" resource
            # track download count
            res.update_download_count()

            # invoke X-Accel-Redirect on physical vault file in nginx
            response = HttpResponse(content_type=mtype)
            response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
                name=output_path.split('/')[-1])
            response['Content-Length'] = flen
            response['X-Accel-Redirect'] = os.path.join(
                getattr(settings, 'IRODS_USER_URI', '/irods-user'), output_path)
            if __debug__:
                logger.debug("Reverse proxying user {}".format(response['X-Accel-Redirect']))
            return response

    # if we get here, none of the above conditions are true
    # if reverse proxy is enabled, then this is because the resource is remote and federated
    # OR the user specifically requested a non-proxied download.

    options = ('-',)  # we're redirecting to stdout.
    # this unusual way of calling works for streaming federated or local resources
    if __debug__:
        logger.debug("Locally streaming {}".format(output_path))
    # track download count
    res.update_download_count()
    proc = session.run_safe('iget', None, irods_output_path, *options)
    response = FileResponse(proc.stdout, content_type=mtype)
    response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
        name=output_path.split('/')[-1])
    response['Content-Length'] = flen
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
