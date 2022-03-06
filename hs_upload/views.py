from django.http import HttpResponse
from rest_framework.decorators import api_view
from django.views.generic.base import TemplateView
from django_irods import icommands

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from drf_yasg.utils import swagger_auto_schema

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
            return response

        istorage = res.get_irods_storage()  # deal with federated storage
        irods_path = res.get_irods_path(path, prepend_short_id=False)

        if not istorage.exists(irods_path):
            response = HttpResponse(status=401)
            content_msg = "Path {} must already exist!".format(path)
            response.content = content_msg
            return response

        try:
            istorage.listdir(irods_path)  # is this a folder?
        except icommands.SessionException:
            response = HttpResponse(status=401)
            content_msg = "Path {} is not a folder!".format(path)
            response.content = content_msg
            return response

        # fully authorized: generate the view, including calling get_context_data below.
        return super(UploadContextView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['path'] = kwargs['path']  # guaranteed to succeed and exist
        return context
