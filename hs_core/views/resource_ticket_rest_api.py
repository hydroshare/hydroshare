import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework import status

from django.core.exceptions import SuspiciousFileOperation, ValidationError

from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE

from django_irods.icommands import SessionException

# hsapi/resource/{pk}/ticket/read/{path}
#   GET: create
# hsapi/resource/{pk}/ticket/write/{path} (currently disabled)
#   GET: create
# hsapi/resource/{pk}/ticket/bag
#   GET: create
# hsapi/resource/{pk}/ticket/info/{tnumber}
#   GET: list
#   DELETE: remove


class CreateResourceTicket(APIView):
    """
    Create resource iRODS tickets via REST

    REST URL: hsapi/resource/{pk}/{op}/{path}/
    HTTP methods: GET
    Returns HTTP 201, 400, 403, 404

    An example of a correct query is:

    GET /hsapi/resource/ff243faf8ab84adc999e5233091f2322/ticket/read/data/contents/cea.tif/

    This returns HTTP_201_CREATED with content:
    {u'operation': u'read',
     u'path':
         u'/hydroshareZone/home/cuahsi2DataProxy/ff243faf8ab84adc999e5233091f2322/data/\
         contents/cea.tif',
     u'resource_id': u'ff243faf8ab84adc999e5233091f2322',
     u'ticket_id': u'Kj8kock9aaeszyN'}

    Error returns 400, 403, 404 return a string with the error message instead of JSON.
    """

    allowed_methods = ('GET',)

    def get(self, request, pk, op, pathname):
        """
        create a ticket for a specific file or folder

        :param pk: key of resource for which to issue ticket
        :param op: operation: 'read' or 'write'
        :param pathname: path for which to issue ticket. If empty, whole data directory is assumed.
        """
        if op != 'read' and op != 'write':
            return Response("Operation must be read or write", status=status.HTTP_400_BAD_REQUEST)

        write = (op == 'write')
        needed_permission = ACTION_TO_AUTHORIZE.EDIT_RESOURCE if write \
            else ACTION_TO_AUTHORIZE.VIEW_RESOURCE

        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=needed_permission, raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized:
            return Response("Insufficient permission", status=status.HTTP_403_FORBIDDEN)

        try:
            view_utils.irods_path_is_allowed(pathname)  # check for hacking attempts
        except (ValidationError, SuspiciousFileOperation) as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)

        if pathname is not None and pathname != '':
            fullpath = os.path.join(resource.root_path, pathname)
        elif op == 'read':  # allow reading anything in path
            fullpath = resource.root_path
        else:  # op == 'write'
            return Response("Write operation must specify path", status=status.HTTP_400_BAD_REQUEST)

        # TODO: check for folder support before allowing folders to be written to
        # The API allows existing files that should not exist to be read anyway.
        # It should not allow files that should not exist to be created.

        try:
            ticket, abspath = resource.create_ticket(request.user, path=fullpath, write=write)
        except SessionException as e:
            return Response(e.stderr, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'resource_id': pk,
             'path': abspath,
             'ticket_id': ticket,
             'operation': op},
            status=status.HTTP_201_CREATED)


class CreateBagTicket(APIView):
    """
    Create bag iRODS tickets via REST

    REST URL: hsapi/resource/{pk}/bag/
    HTTP methods: GET
    Returns HTTP 201, 400, 403, 404

    Example of a correct request:
    GET /hsapi/resource/28f87079ceaf440588e7866a0f4b6c57/ticket/bag/

    This returns HTTP_201_CREATED with content:
    {u'operation': u'read',
     u'path': u'/hydroshareZone/home/cuahsi2DataProxy/bags/28f87079ceaf440588e7866a0f4b6c57.zip',
     u'resource_id': u'28f87079ceaf440588e7866a0f4b6c57',
     u'ticket_id': u'pwYwPanpnwdDZa9'}

    Error returns 400, 403, 404 return a string with the error message instead of JSON.
    """
    allowed_methods = ('GET',)

    def get(self, request, pk):
        """
        create a ticket for a bag

        :param pk: key of resource for which to issue ticket
        :param pathname: path for which to issue ticket. If empty, whole data directory is assumed.
        """
        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized:
            return Response("Insufficient permission", status=status.HTTP_403_FORBIDDEN)

        fullpath = resource.bag_path
        try:
            ticket, abspath = resource.create_ticket(request.user, path=fullpath, write=False)
        except SessionException as e:
            return Response(e.stderr, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response(e.message, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'resource_id': pk,
             'path': abspath,
             'ticket_id': ticket,
             'operation': 'read'},
            status=status.HTTP_201_CREATED)


class ManageResourceTicket(APIView):
    """
    list or delete a ticket

    Methods: GET, DELETE
    Returns: HTTP 200, 400, 403, 403

    Example of a correct list request:

    GET /hsapi/resource/28f87079ceaf440588e7866a0f4b6c57/ticket/info/pwYwPanpnwdDZa9/

    This returns HTTP_200_OK with content:

    {u'expires': u'2017-07-26.00:17:00',
     u'filename': u'28f87079ceaf440588e7866a0f4b6c57.zip',
     u'full_path':
         u'/hydroshareZone/home/cuahsi2DataProxy/bags/28f87079ceaf440588e7866a0f4b6c57.zip',
     u'id': u'457392',
     u'obj type': u'data',
     u'owner': u'cuahsi2DataProxy',
     u'ticket_id': u'pwYwPanpnwdDZa9',
     u'type': u'read',
     u'uses count': u'0',
     u'uses limit': u'1',
     u'write byte count': u'0',
     u'write byte limit': u'0',
     u'write file count': u'0',
     u'write file limit': u'10',
     u'zone': u'hydroshareZone'}

    Example of deleting the same ticket:

    DELETE /hsapi/resource/28f87079ceaf440588e7866a0f4b6c57/ticket/info/pwYwPanpnwdDZa9/

    This returns HTTP_200_OK with content:

    {u'expires': u'2017-07-26.00:17:00',
     u'filename': u'28f87079ceaf440588e7866a0f4b6c57.zip',
     u'full_path':
         u'/hydroshareZone/home/cuahsi2DataProxy/bags/28f87079ceaf440588e7866a0f4b6c57.zip',
     u'id': u'457392',
     u'obj type': u'data',
     u'owner': u'cuahsi2DataProxy',
     u'ticket_id': u'pwYwPanpnwdDZa9',
     u'type': u'read',
     u'uses count': u'0',
     u'uses limit': u'1',
     u'write byte count': u'0',
     u'write byte limit': u'0',
     u'write file count': u'0',
     u'write file limit': u'10',
     u'zone': u'hydroshareZone'}

    This is the same content as before, just before the DELETE.

    Error returns 400, 403, 404 return a string with the error message instead of JSON.
    """

    allowed_methods = ('GET', 'DELETE')

    def get(self, request, pk, ticket):
        """
        list a ticket


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
            return Response(data=resource.list_ticket(ticket), status=status.HTTP_200_OK)
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        except SessionException as ex:
            return Response(ex.stderr, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, ticket):
        """
        Delete a ticket.

        """
        try:
            resource, authorized, user = view_utils.authorize(
                request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                raises_exception=False)
        except NotFound as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        if not authorized:
            return Response("Insufficient permission", status=status.HTTP_401_UNAUTHORIZED)

        # list the ticket details to return to user
        try:
            data = resource.list_ticket(ticket)
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_404_NOT_FOUND)
        except SessionException as ex:
            return Response(ex.stderr, status=status.HTTP_400_BAD_REQUEST)

        # try to delete the ticket; this rejects deletion if user isn't authorized
        try:
            resource.delete_ticket(request.user, ticket)
        except PermissionDenied as ex:
            return Response(ex.stderr, status=status.HTTP_403_PERMISSION_DENIED)
        except ValidationError as ex:
            return Response(ex.message, status=status.HTTP_400_BAD_REQUEST)
        except SessionException as ex:
            return Response(ex.stderr, status=status.HTTP_400_BAD_REQUEST)

        # return ticket details
        return Response(data, status=status.HTTP_200_OK)
