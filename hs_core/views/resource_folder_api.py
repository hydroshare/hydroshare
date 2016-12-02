from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework import status

from django.core.exceptions import SuspiciousFileOperation 

from hs_core import hydroshare
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE

from django_irods.icommands import SessionException


class ResourceFolders(APIView):
    """
    Manipulate resource folders in REST

    REST URL: hsapi/resource/{pk}/folders/{path}/
    HTTP methods: GET, PUT, DELETE
    Returns HTTP 400, 401, 403, 404
    """
    allowed_methods = ('GET', 'PUT', 'DELETE')

    def get(self, request, pk, path):
        """
        list a given folder

        """
        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE, 
                raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized: 
            return Response("Insufficient permission", status=status.HTTP_401_UNAUTHORIZED) 

        try:
            view_utils.irods_path_is_allowed(path)  # check for hacking attempts
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)
        except SuspiciousFileOperation as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)

        if not resource.supports_folders:
            return Response("Resource type does not support subfolders",
                   status=status.HTTP_403_FORBIDDEN)

        try:
            contents = view_utils.list_folder(pk, path)
        except SessionException:
            return Response("Cannot list path", status=status.HTTP_404_NOT_FOUND)

        return Response(
            {'resource_id': pk,
             'path': path,
             'files': contents[1],
             'folders': contents[0]},
            status=status.HTTP_200_OK)

    def put(self, request, pk, path):
        """ create a given folder if not present and allowed

        """
        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE, 
                raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized: 
            return Response("Insufficient permission", status=status.HTTP_401_UNAUTHORIZED) 

        try:
            view_utils.irods_path_is_allowed(path)  # check for hacking attempts
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)
        except SuspiciousFileOperation as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)

        if not resource.supports_folders:
            return Response("Resource type does not support subfolders",
                   status=status.HTTP_403_FORBIDDEN)

        try:
            view_utils.create_folder(pk, path)
        except SessionException:
            raise ValidationError("Cannot create folder")
        return Response(data={'resource_id': pk, 'path': path},
                        status=status.HTTP_201_CREATED)

    def delete(self, request, pk, path):
        """
        Delete a folder.

        """
        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE, 
                raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized: 
            return Response("Insufficient permission", status=status.HTTP_401_UNAUTHORIZED) 

        try:
            view_utils.irods_path_is_allowed(path)  # check for hacking attempts
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)
        except SuspiciousFileOperation as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)

        if not resource.supports_folders:
            return Response("Resource type does not support subfolders",
                            status=status.HTTP_403_FORBIDDEN)

        try:
            view_utils.remove_folder(request.user, pk, path)
        except SessionException:
            return Response("Cannot remove folder", status=status.HTTP_400_BAD_REQUEST)

        view_utils.remove_irods_folder_in_django(resource, resource.get_irods_storage(), path)

        return Response(data={'resource_id': pk, 'path': path},
                        status=status.HTTP_200_OK)
