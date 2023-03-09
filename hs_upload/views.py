from django.http import HttpResponse
# from rest_framework.decorators import api_view
from django.views.generic.base import TemplateView
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
            logger.error(content_msg)
            return response

        path = kwargs['path']
        # logger.debug("request path is '{}'".format(path))

        # remove trailing /'s
        split_path_strs = path.split('/')
        while split_path_strs[-1] == '':
            split_path_strs.pop()
        path = '/'.join(split_path_strs)

        # logger.debug("request path is now '{}'".format(path))

        # TODO: verify that this is a valid file path at time of request.
        # TODO: perhaps create intermediate directories before upload.

        # first path element is resource short_path
        res_id = split_path_strs[0]

        # logger.debug("resource id is {}".format(res_id))

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
        stuff = kwargs['path'].split('/')
        logger.debug(stuff)
        context['folder'] = '/'.join(stuff[2:])
        return context


class UppyView(UploadContextView):
    template_name = 'uppy.html'


def upload_valid(user, path_of_folder, filename):
    """ test that an upload request is allowed """

    path_of_file = os.path.join(path_of_folder, filename)
    stuff = path_of_folder.split('/')
    rid = stuff[0]

    logger.debug("tusd upload start:  rid = {}, path_of_folder = {}, filename = {}"
                 .format(rid, path_of_folder, filename))

    # check that resource exists
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)
        return response

    if not user.uaccess.can_change_resource(resource):
        response = HttpResponse(status=404)
        content_msg = "user {} cannot add files to resource {}".format(user.username, rid)
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

    return None  # all checks pass


# TODO: need to link the tmpfile and Upload record for in-progress uploads.
# TODO: this needs to only be done once. This requires using the Progress response.


def cleanup(resource, path, tmpfile):
    """ clean up after a failed upload """
    # delete lock record
    if resource is not None:
        try:
            Upload.remove(resource, path)
            # logger.debug("deleted resource {}/path {}".format(resource.short_id, path))
        except Upload.DoesNotExist:  # not an error for lockfile not to exist
            pass
            # logger.debug("resource {} or path {} does not exist".format(resource.short_id, path))
    if tmpfile is not None:
        try:
            os.remove(tmpfile)
        except Exception as e:
            logger.error("can't remove file {}: {}".format(tmpfile, str(e)))
        try:
            os.remove(tmpfile + '.info')
        except Exception as e:
            logger.error("can't remove file {}: {}".format(tmpfile, str(e)))


def print_all():
    """ print all uploads in progress """
    print("existing lockfiles")
    for o in Upload.objects.all():
        print("resource {} path {} user {}".format(o.resource.short_id, o.path, o.user.username))
    print("tusd uploads in progress")
    for file in os.listdir("/tusd_tmp"):
        if file != "tusd.sock":
            print("{}".format(file))


def debug_all():
    """ log all uploads in progress """
    logger.debug("existing lockfiles")
    for o in Upload.objects.all():
        logger.debug("resource {} path {} user {}".format(o.resource.short_id, o.path, o.user.username))
    logger.debug("tusd uploads in progress")
    for file in os.listdir("/tusd_tmp"):
        if file != "tusd.sock":
            logger.debug("{}".format(file))


def clear_all():
    """ clear the queue of uploads """
    # remove all locks
    Upload.objects.all().delete()
    # remove all uploads in progress
    for file in os.listdir("/tusd_tmp"):
        if file != "tusd.sock":
            os.remove(os.path.join("/tusd_tmp", file))


def start(request, path_of_folder, *args, **kwargs):
    """
    check whether an upload file name is acceptable
    This checks every aspect of the upload, including user permissions,
    whether the file already exists in the target directory, etc.

    This has the side-effect of registering the upload as in-progress
    if the upload is allowed.

    This can be used for both uppy and non-uppy
    uploads, as it has no dependence upon uppy to be useful.
    """

    user = request.user
    filename = request.GET.get('filename')
    filesize = request.GET.get('filesize')
    logger.debug("upload start user={} path={} filename={}"
                 .format(user.username, path_of_folder, filename))

    # if the upload isn't valid, return a response object with an error.
    response = upload_valid(user, path_of_folder, filename)
    if response is not None:   # error encountered
        return response        # deny upload

    path_split = path_of_folder.split('/')
    rid = path_split[0]
    path_of_file = os.path.join(path_of_folder, filename)

    # locate the resource.
    # needed when creating the upload lock.
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=404)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # OK so far: upload in progress should not exist
    # This must be checked here rather than in upload_valid, because it isn't used in all cases.
    if Upload.exists(resource, path_of_file):
        response = HttpResponse(status=401)
        content_msg = "upload to resource {} path {} already in progress!".format(rid, path_of_file)
        response.content = content_msg
        logger.error(content_msg)
        return response

    # create an upload lock
    try:
        # logger.debug("creating upload lock user={} resource={} path={}"
        #              .format(user.username, resource.short_id, path_of_file))
        Upload.create(user, resource, path_of_file, filesize)
        return HttpResponse(status=200)  # ok to proceed
    except Exception as e:
        response = HttpResponse(status=401)
        content_msg = "cannot initiate upload: {}".format(e)
        response.content = content_msg
        logger.error(content_msg)
        return response


def stop(request, path_of_folder, *args, **kwargs):
    """
    Stop processing of an upload.

    This is used to inform Django that an upload is no longer pending. It
    marks an upload is not in progress, either by completing it elsewhere
    or by uppy marking it as aborted.

    We do not validate aborts because we always want to abort if someone asks to.

    This does not copy a uppy file into its resource.  If you use this on a completed
    uppy upload, the upload will be aborted and deleted.

    For uppy uploads, use finish instead.
    """

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

    logger.debug("upload abort: resource={}, folder={} file={}"
                 .format(rid, path_of_folder, filename))

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
    cleanup(resource, path_of_file, tusd_path_of_file)
    if response is not None:
        return response
    else:
        return HttpResponse(status=200)  # no content body needed


def finish(request, path_of_folder, *args, **kwargs):
    """
    finish processing an upload
    This includes copying the file from a designated holding location into iRODS
    and into the resource in question.  If this is accomplished by other means,
    use stop instead.
    """
    user = request.user
    filename = request.GET.get('filename')
    # filesize = request.GET.get('filesize')
    path_of_file = os.path.join(path_of_folder, filename)
    path_split = path_of_folder.split('/')
    rid = path_split[0]
    logger.debug("upload finish user={} folder={} file={}"
                 .format(user.username, path_of_folder, filename))

    response = None  # no error so far

    # does the resource exist? Needed for cleanup in case the response is an error
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.error(content_msg)

    # recover tusd filename from URL; needed for cleanup in case the response is an error
    tusd_url = request.GET.get('url')
    if tusd_url is None:
        tusd_path_of_file = None
        content_msg = "url for tusd file is not specified!"
        logger.error(content_msg)
        if response is None:
            response = HttpResponse(status=403)
            response.content = content_msg
    else:
        tusd_filename = tusd_url.split('/')[-1]
        tusd_path_of_file = os.path.join('/tusd_tmp', tusd_filename)

    # uploaded file must still exist as a source
    if not os.path.exists(tusd_path_of_file):
        content_msg = "uploaded file {} does not exist!".format(tusd_path_of_file)
        logger.error(content_msg)
        tusd_path_of_file = None
        if response is None:
            response = HttpResponse(status=403)
            response.content = content_msg

    # if the upload isn't allowed, return a response object with an error.
    if response is None:
        response = upload_valid(user, path_of_folder, filename)

    # Now we're ready to clean up after a rejected response
    if response is not None:
        cleanup(resource, path_of_file, tusd_path_of_file)
        return response

    # now we are sure the request is valid in all ways; perform the request

    # needed for irods copy.
    relative_path_of_folder = '/'.join(path_split[3:])  # without data/contents/

    # all tests pass: move into appropriate location
    logger.debug("upload copy uploaded file {} to {}".format(tusd_path_of_file, path_of_file))
    # use standard HydroShare file ingestion.
    upload_object = UploadedFile(file=open(tusd_path_of_file, mode="rb"), name=filename)
    add_file_to_resource(resource, upload_object, folder=relative_path_of_folder)

    # delete intermediary file and lock.
    cleanup(resource, path_of_file, tusd_path_of_file)

    # return OK status
    return HttpResponse(status=200)  # no content body needed
