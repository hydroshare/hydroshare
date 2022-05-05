from django.http import HttpResponse
# from rest_framework.decorators import api_view
from django.views.generic.base import TemplateView
from django.conf import settings
from django_irods import icommands
from hs_core.models import BaseResource
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import get_resource_by_shortkey
from hs_upload.models import Upload
from django.core.files.uploadedfile import UploadedFile
from hs_core.hydroshare.utils import add_file_to_resource

import os
import logging
logger = logging.getLogger(__name__)


class UploadContextView(TemplateView):
    """ generate a form to start the upload as a separate JavaScript.
    :param request: the request object
    :param path: the path of the folder in which the upload should be placed.

    This builds a JavaScript environment on the client browser that handles uploads.
    It checks the upload request for validity and -- if valid -- loads all context needed.
    The argument `path` says where in what resource the file should be stored, and is of the form
        `{resource-id}/data/contents/subpath`
    The path must exist.

    Given this path, this JavaScript template builds a query form that asks the user
    for a filename and then places it here in this path under the same name.  The file
    must not already exist on the path.

    The logic in this script is complex:
        1. Authorize write access to the target path.
        2. Display the target path.
        2. Ask the user for a local file.
        3. Begin uploading the file via a reverse proxy call to tusd via NGINX.
        4. Upon completion, call complete below to complete the upload.
        5. This script must remain open until the upload completes.

    Because of this complexity, this view has to retain the context of the complete upload, including
        1. The identity of the local file.
        2. The remote destination path.
        3. The state of the upload.
        4. The temporary file chosen to store the upload until completion.

    """
    template_name = "context.html"
    http_method_names = ["get"]

    def dispatch(self, *args, **kwargs):
        """ before dispatching normally, authenticate request """

        if 'path' not in kwargs:
            response = HttpResponse(status=401)
            content_msg = "No upload path specified!"
            response.content = content_msg
            logger.debug(content_msg)
            return response

        path = kwargs['path']
        logger.debug("request path is '{}'".format(path))

        # remove trailing /'s
        split_path_strs = path.split('/')
        while split_path_strs[-1] == '':
            split_path_strs.pop()
        path = '/'.join(split_path_strs)

        logger.debug("request path is now '{}'".format(path))

        # TODO: verify that this is a valid file path at time of request.
        # TODO: perhaps create intermediate directories before upload.

        # first path element is resource short_path
        res_id = split_path_strs[0]

        logger.debug("resource id is {}".format(res_id))

        # now we have the resource Id and can authorize the request
        # if the resource does not exist in django, authorized will be false
        resource, authorized, _ = authorize(self.request, res_id,
                                            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                            raises_exception=False)
        if not authorized:
            response = HttpResponse(status=401)
            content_msg = "You do not have permission to upload files to resource {}!".format(res_id)
            response.content = content_msg
            logger.error(content_msg)
            return response

        istorage = resource.get_irods_storage()  # deal with federated storage
        irods_path = resource.get_irods_path(path, prepend_short_id=False)

        if not istorage.exists(irods_path):
            response = HttpResponse(status=401)
            content_msg = "Path {} must already exist!".format(path)
            response.content = content_msg
            logger.error(content_msg)
            return response

        try:
            istorage.listdir(irods_path)  # is this a folder?
        except icommands.SessionException:
            response = HttpResponse(status=401)
            content_msg = "Path {} is not a folder!".format(path)
            response.content = content_msg
            logger.error(content_msg)
            return response

        # fully authorized: generate the view, including calling get_context_data below.
        kwargs['resource'] = resource
        return super(UploadContextView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['path'] = kwargs['path']  # guaranteed to succeed and exist
        context['resource'] = kwargs['resource']
        context['FQDN_OR_IP'] = getattr(settings, 'FQDN_OR_IP', 'www.hydroshare.org')
        logger.debug("FQDN_OR_IP is '{}'".format(context['FQDN_OR_IP']))
        return context


class UppyView(UploadContextView):
    template_name = 'uppy.html'


def start(request, path_of_folder, *args, **kwargs):
    """ check whether upload file name is acceptable """

    user = request.user
    logger.debug("start request user {} path {}".format(user.username, path_of_folder))
    filename = request.GET.get('filename')
    filesize = request.GET.get('filesize')
    stuff = path_of_folder.split('/')
    rid = stuff[0]
    logger.debug("tusd upload start:  rid = {}, path_of_folder = {}, filename = {}"
                 .format(rid, path_of_folder, filename))
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # file path_of_folder should start with data/contents
    if stuff[1] != 'data' or stuff[2] != 'contents':
        response = HttpResponse(status=401)
        content_msg = "path {} must start with 'data/contents/'!".format(path_of_folder)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # file path_of_folder should exist
    istorage = resource.get_irods_storage()
    irods_path_of_folder = resource.get_irods_path(path_of_folder)
    if not istorage.exists(irods_path_of_folder):
        response = HttpResponse(status=401)
        content_msg = "target folder '{}' does not exist!".format(path_of_folder)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # file name should not exist
    path_of_file = os.path.join(path_of_folder, filename)
    irods_path_of_file = resource.get_irods_path(path_of_file)
    if istorage.exists(irods_path_of_file):
        response = HttpResponse(status=401)
        content_msg = "file '{}' already exists!".format(path_of_file)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # upload in progress should not exist
    # TODO: fold this code into Upload.create under an atomic transaction
    if Upload.exists(resource, path_of_file):
        response = HttpResponse(status=401)
        content_msg = "upload to resource {} path {} already in progress!".format(rid, path_of_file)
        response.content = content_msg
        logger.error(content_msg)
        return response

    try:
        logger.debug("creating upload user={} resource={} path={}"
                     .format(user.username, resource.short_id, path_of_file))
        Upload.create(user, resource, path_of_file, filesize)
        return HttpResponse(status=200)  # ok to proceed
    except Exception as e:
        response = HttpResponse(status=401)
        content_msg = "cannot initiate upload: {}".format(e)
        response.content = content_msg
        logger.error(content_msg)
        return response


# TODO: need to link the tmpfile and Upload record for in-progress uploads.
# TODO: this needs to only be done once. This requires using the Progress response.
def cleanup(resource, path, tmpfile):
    """ clean up after a failed upload """
    # delete lock record
    if resource is not None:
        try:
            Upload.remove(resource, path)
            logger.debug("deleted resource {}/path {}".format(resource.short_id, path))
        except Upload.DoesNotExist:  # not an error for lockfile not to exist
            logger.debug("resource {} or path {} does not exist".format(resource.short_id, path))
    if tmpfile is not None:
        try:
            os.remove(tmpfile)
        except Exception as e:
            logger.debug("can't remove file {}: {}".format(tmpfile, str(e)))
        try:
            os.remove(tmpfile + '.info')
        except Exception as e:
            logger.debug("can't remove file {}: {}".format(tmpfile, str(e)))


def abort(request, path_of_folder, *args, **kwargs):
    """ abort processing of an upload """
    # user = request.user
    filename = request.GET.get('filename')
    # filesize = request.GET.get('filesize')
    # when aborting a request that is pending, there is no URL.
    url = request.GET.get('url')
    if url is not None:
        tusd_root = url.split('/')[-1]
        tusd_path_of_file = os.path.join('/tusd_tmp', tusd_root)
    else:
        tusd_root = None
        tusd_path_of_file = None
    path_split = path_of_folder.split('/')
    rid = path_split[0]
    path_of_file = os.path.join(path_of_folder, filename)
    response = None  # so far, no errors
    resource = None  # unknown whether resource has been deleted.
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)

    # TODO: make sure that Upload has cascade delete enabled, so that deleting a
    # TODO: resource causes deletion of the Upload record for the resource.
    logger.debug("tusd upload abort:  rid = {}, path = {}"
                 .format(rid, path_of_file))
    cleanup(resource, path_of_file, tusd_path_of_file)
    if response is not None:
        return response
    else:
        return HttpResponse(status=200)  # no content body needed


def finish(request, path_of_folder, *args, **kwargs):
    """ finish processing an upload """
    user = request.user
    filename = request.GET.get('filename')
    # filesize = request.GET.get('filesize')
    path_of_file = os.path.join(path_of_folder, filename)

    # recover tusd filename from URL
    tusd_url = request.GET.get('url')
    tusd_filename = tusd_url.split('/')[-1]
    tusd_path_of_file = os.path.join('/tusd_tmp', tusd_filename)

    path_split = path_of_folder.split('/')
    rid = path_split[0]
    logger.debug("finish request user {} path {} tusd {}".format(user.username, path_of_file, tusd_path_of_file))

    # begin request validation.
    # first, does the resource exist?
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # needed for irods copy.
    relative_path_of_folder = '/'.join(path_split[3:])  # without data/contents/

    logger.debug("tusd upload finish:  rid = {}, path = {}, filename = {}, tusd_file = {}"
                 .format(rid, path_of_folder, filename, tusd_path_of_file))

    # uploaded file must still exist as a source
    if not os.path.exists(tusd_path_of_file):
        response = HttpResponse(status=401)
        content_msg = "uploaded file {} does not exist!".format(tusd_path_of_file)
        response.content = content_msg
        logger.error(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # now we have the resource Id and can authorize the request
    # if the resource does not exist in django, authorized will be false
    resource, authorized, _ = authorize(request, rid,
                                        needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                        raises_exception=False)
    if not authorized:
        response = HttpResponse(status=401)
        content_msg = "You do not have permission to upload files to resource {}!".format(rid)
        response.content = content_msg
        logger.error(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    istorage = resource.get_irods_storage()  # deal with federated storage
    irods_path_of_folder = resource.get_irods_path(path_of_folder)

    # folder should exist in resource
    if not istorage.exists(irods_path_of_folder):
        response = HttpResponse(status=401)
        content_msg = "Folder {} must already exist!".format(irods_path_of_folder)
        response.content = content_msg
        logger.error(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # folder name should correspond to a folder
    try:
        istorage.listdir(irods_path_of_folder)  # is this a folder?
    except icommands.SessionException:
        response = HttpResponse(status=401)
        content_msg = "Path {} is not a folder!".format(path_of_folder)
        response.content = content_msg
        logger.debug(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # file should not exist in resource
    irods_path_of_file = os.path.join(irods_path_of_folder, filename)
    logger.debug("irods_path including file is {}".format(irods_path_of_file))
    if istorage.exists(irods_path_of_file):
        response = HttpResponse(status=401)
        content_msg = "Path {} already exists!".format(path_of_file)
        response.content = content_msg
        logger.error(content_msg)
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # all tests pass: move into appropriate location
    logger.debug("copy uploaded file {} to {}".format(tusd_path_of_file, path_of_file))
    upload_object = UploadedFile(file=open(tusd_path_of_file, mode="rb"), name=filename)
    add_file_to_resource(resource, upload_object, folder=relative_path_of_folder)

    # delete intermediary file and lock.
    cleanup(resource, path_of_file, tusd_path_of_file)
    return HttpResponse(status=200)  # no content body needed


def print_all():
    """ print all uploads in progress """
    print("existing lockfiles")
    for o in Upload.objects.all():
        print("resource {} path {} user {}".format(o.resource.short_id, o.path, o.user.username))
    print("tusd uploads in progress")
    for file in os.listdir("/tusd_tmp"):
        if file != "tusd.sock":
            print("{}".format(file))


def clear_all():
    """ clear the queue of uploads """
    # remove all locks
    Upload.objects.all().delete()
    # remove all uploads in progress
    for file in os.listdir("/tusd_tmp"):
        if file != "tusd.sock":
            os.remove(os.path.join("/tusd_tmp", file))
