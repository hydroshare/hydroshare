from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status

from hs_core import hydroshare
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE

from django.core.exceptions import SessionException


class ResourceFolders(APIView):
    """
    Manipulate resource folders in REST

    REST URL: hsapi/resource/{pk}/folders/{path}/
    HTTP methods: GET, PUT, DELETE
    """
    allowed_methods = ['GET', 'PUT', 'DELETE']

    def get(self, request, pk, path):
        """
        list a given folder

        This is limited by the capabilites of the current iRODS API.
        It can't really tell that you asked to list a file rather than a folder.

        """
        view_utils.authorize(
            request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        view_utils.irods_path_is_allowed(path)  # check for hacking attempts
        try:
            contents = view_utils.list_folder(request.user, pk, path)
        except SessionException:
            raise ValidationError("Cannot list path")

        resource = hydroshare.get_resource_from_id(pk)
        if not resource.supports_folders:
            raise ValidationError("Resource type does not support subfolders")

        return Response(
            data={
                'resource_id': pk,
                'path': path,
                'contents': {
                    'files': contents[1],
                    'folders': contents[0]}},
            status=status.HTTP_200_OK)

    def put(self, request, pk, path):
        """ create a given folder if not present and allowed

        This is limited by the capabilites of the current iRODS API.
        It can't really tell whether a folder exists because there is
        currently no method to determine whether a path points to a
        folder or a file. In both cases, it will return OK.

        """
        view_utils.authorize(
            request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
        view_utils.irods_path_is_allowed(path)  # check for hacking attempts
        resource = hydroshare.get_resource_from_id(pk)

        if not resource.supports_folders:
            raise ValidationError("Resource type does not support subfolders")

        try:
            view_utils.list_folder(request.user, pk, path)
            # if it already exists, do nothing
            return Response(data={'resource_id': pk, 'path': path},
                            status=status.HTTP_200_OK)
        except SessionException:
            # If this fails, create folder
            pass

        try:
            view_utils.create_folder(request.user, pk, path)
        except SessionException:
            raise ValidationError("Cannot create folder")
        return Response(data={'resource_id': pk, 'path': path},
                        status=status.HTTP_201_CREATED)

    def delete(self, request, pk, path):
        """
        Delete a folder.

        This is limited by the capabilites of the current iRODS API.
        It can't tell that what it is removing is a folder;
        the list_folder command returns ambiguous results.
        It simply removes what it gets.

        """
        view_utils.authorize(
            request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        view_utils.irods_path_is_allowed(path)  # check for hacking attempts

        try:
            view_utils.list_folder(request.user, pk, path)
        except SessionException:
            raise ValidationError("Cannot list contents of path")

        resource = hydroshare.get_resource_from_id(pk)
        if not resource.supports_folders:
            raise ValidationError("Resource type does not support subfolders")

        try:
            view_utils.remove_folder(request.user, pk, path)
        except SessionException:
            raise ValidationError("Cannot remove folder")
        view_utils.remove_irods_folder_in_django(resource, resource.get_irods_storage(), path)

        return Response(data={'resource_id': pk, 'path': path},
                        status=status.HTTP_200_OK)
