from django.http import HttpResponse
# from rest_framework.decorators import api_view
from django.views.generic.base import TemplateView
from django.conf import settings
from django_irods import icommands
from hs_core.models import BaseResource
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare import get_resource_by_shortkey
from hs_upload.models import Upload

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
        res, authorized, _ = authorize(self.request, res_id,
                                       needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                       raises_exception=False)
        if not authorized:
            response = HttpResponse(status=401)
            content_msg = "You do not have permission to upload files to resource {}!".format(res_id)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        istorage = res.get_irods_storage()  # deal with federated storage
        irods_path = res.get_irods_path(path, prepend_short_id=False)

        if not istorage.exists(irods_path):
            response = HttpResponse(status=401)
            content_msg = "Path {} must already exist!".format(path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        try:
            istorage.listdir(irods_path)  # is this a folder?
        except icommands.SessionException:
            response = HttpResponse(status=401)
            content_msg = "Path {} is not a folder!".format(path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        # fully authorized: generate the view, including calling get_context_data below.
        return super(UploadContextView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['path'] = kwargs['path']  # guaranteed to succeed and exist
        return context


def nameok(request, path, *args, **kwargs):
    """ check whether upload file name is acceptable """

    user = request.user
    filename = request.GET.get('filename')
    size = request.GET.get('size')
    rid = path.split('/')[0]
    try:
        resource = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.debug(content_msg)
        return response

    # file path should exist
    istorage = resource.get_irods_storage()
    irods_path = resource.get_irods_path(path)
    if not istorage.exists(irods_path):
        response = HttpResponse(status=401)
        content_msg = "target folder {} does not exist!".format(irods_path)
        response.content = content_msg
        logger.debug(content_msg)
        return response

    # file name should not exist
    path = os.path.join(path, filename)
    irods_path = resource.get_irods_path(path)
    if istorage.exists(irods_path):
        response = HttpResponse(status=401)
        content_msg = "resource file {} already exists!".format(rid)
        response.content = content_msg
        logger.debug(content_msg)
        return response

    # upload in progress should not exist
    # TODO: fold this code into Upload.create under an atomic transaction
    path = os.path.join(path, filename)
    in_progress = Upload.objects.get(resource=resource, path=path).exists()
    if in_progress:
        response = HttpResponse(status=401)
        content_msg = "upload to resource {} path {} already in progress!".format(rid, path)
        response.content = content_msg
        logger.debug(content_msg)
        return response

    try:
        Upload.create(user, resource, path, size)
        return HttpResponse(status=200)  # ok to proceed
    except Exception as e:
        response = HttpResponse(status=401)
        content_msg = "cannot initiate upload: {}".format(e)
        response.content = content_msg
        logger.debug(content_msg)
        return response


def event(request, path, *args, **kwargs):
    """ consume a tusd event """
    # user = request.user
    event = request.GET.get('event')
    filename = request.GET.get('filename')
    filetype = request.GET.get('filetype')
    uploaded = request.GET.get('uploaded')
    size = request.GET.get('size')
    url = request.GET.get('url')

    path = path.split('/')
    rid = path[0]
    try:
        _ = get_resource_by_shortkey(rid, or_404=False)
    except BaseResource.DoesNotExist:
        response = HttpResponse(status=403)
        content_msg = "resource {} does not exist!".format(rid)
        response.content = content_msg
        logger.debug(content_msg)
        return response

    path = '/'.join(path[1:])

    logger.debug("tusd event = {},  rid = {}, path = {}, filename = {}, filetype = {}, url = {}"
                 .format(event, rid, path, filename, filetype, url))
    if uploaded is not None:
        logger.debug("tusd event = {}, bytes uploaded = {}, size = {}".format(event, uploaded, size))

    if event == 'success':

        # now we have the resource Id and can authorize the request
        # if the resource does not exist in django, authorized will be false
        res, authorized, _ = authorize(request, rid,
                                       needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                                       raises_exception=False)
        if not authorized:
            response = HttpResponse(status=401)
            content_msg = "You do not have permission to upload files to resource {}!".format(rid)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        istorage = res.get_irods_storage()  # deal with federated storage
        irods_path = res.get_irods_path(path)

        # folder should exist in resource
        if not istorage.exists(irods_path):
            response = HttpResponse(status=401)
            content_msg = "Folder {} must already exist!".format(irods_path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        # folder name should correspond to a folder
        try:
            istorage.listdir(irods_path)  # is this a folder?
        except icommands.SessionException:
            response = HttpResponse(status=401)
            content_msg = "Path {} is not a folder!".format(path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        # file should not exist in resource
        irods_path = os.path.join(irods_path, filename)
        logger.debug("irods_path including file is {}".format(irods_path))
        if istorage.exists(irods_path):
            response = HttpResponse(status=401)
            content_msg = "Path {} already exists!".format(irods_path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        # uploaded file must still exist as a source
        tusd_root = url.split('/')[-1]
        tusd_path = os.path.join(settings.IRODS_HOME_COLLECTION, 'tusd', tusd_root)
        if not istorage.exists(tusd_path):
            response = HttpResponse(status=401)
            content_msg = "uploaded file {} does not exist!".format(tusd_path)
            response.content = content_msg
            logger.debug(content_msg)
            return response

        # all tests pass: move into appropriate location
        logger.debug("move uploaded file {} to {}".format(tusd_path, irods_path))
        istorage.moveFile(tusd_path, irods_path)

    return HttpResponse(status=200)  # no content body needed
