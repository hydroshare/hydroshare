
from rest_framework.response import Response
from rest_framework import generics, serializers
from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare import utils
from hs_access_control.models import UserResourcePrivilege, GroupResourcePrivilege, \
    PrivilegeCodes, UserAccess
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE


class PrivilegeField(serializers.Field):
    def to_representation(self, privilege):
       return PrivilegeCodes.PRIVILEGE_CHOICES[privilege-1][1]


class GroupResourcePrivilegeSerializer(serializers.ModelSerializer):
    privilege = PrivilegeField()

    class Meta:
        model = GroupResourcePrivilege
        fields = ('id', 'privilege', 'group', 'resource', 'grantor')


class UserResourcePrivilegeSerializer(serializers.ModelSerializer):
    privilege = PrivilegeField()

    class Meta:
        model = UserResourcePrivilege
        fields = ('id', 'privilege', 'user', 'resource', 'grantor')


class ResourceAccessUpdateDelete(generics.RetrieveUpdateDestroyAPIView):
    """
    Read, update, or delete a resource

    REST URL: hsapi/resource/{pk}
    HTTP method: GET
    :return: (on success): The resource in zipped BagIt format.

    REST URL: hsapi/resource/{pk}
    HTTP method: DELETE
    :return: (on success): JSON string of the format: {'resource_id':pk}

    REST URL: hsapi/resource/{pk}
    HTTP method: PUT
    :return: (on success): JSON string of the format: {'resource_id':pk}

    :type   str
    :param  pk: resource id
    :rtype:  JSON string for http methods DELETE and PUT, and resource file data bytes for GET

    :raises:
    NotFound: return JSON format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return JSON format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return JSON format: {parameter-1': ['error message-1'], 'parameter-2':
    ['error message-2'], .. }

    :raises:
    ValidationError: return json format: {'parameter-1':['error message-1'], 'parameter-2':
    ['error message-2'], .. }
    """

    serializer_class = UserResourcePrivilegeSerializer

    allowed_methods = ('GET', 'PUT', 'DELETE')

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE_ACCESS)

        user_resource_serializer, group_resource_serializer = self.get_serializer_classes()
        user_resource_privilege, group_resource_privilege = self.get_queryset(pk, request.user)

        response_data = dict()
        response_data['users'] = user_resource_serializer(user_resource_privilege, many=True).data
        if "groups" in request.query_params.keys() and group_resource_privilege:
            response_data['groups'] = group_resource_serializer(group_resource_privilege, many=True).data

        return Response(data=response_data, status=status.HTTP_200_OK)

    def get_serializer_classes(self):
        return (UserResourcePrivilegeSerializer, GroupResourcePrivilegeSerializer,)

    def get_queryset(self, pk, user):
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)

        if resource.user_id == user.id:
            querysets = (
                UserResourcePrivilege.objects.filter(resource=resource),
                GroupResourcePrivilege.objects.filter(resource=resource)
            )
        else:
            querysets = (
                UserResourcePrivilege.objects.filter(resource=resource, user=user),
                None
            )

        return querysets

    def delete(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE_ACCESS)
        keys = request.query_params.keys()
        user_access = UserAccess(user=request.user)
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)

        if "user_id" in keys and "group_id" in keys:
            return Response(
                data={'error': "Request cannot contain both a 'user' and a 'group' parameter."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if "user_id" in keys:
            user_to_remove = utils.user_from_id(request.query_params['user_id'])
            user_access.unshare_resource_with_user(resource, user_to_remove)
            return Response(
                data={'success': "Resource access privileges removed."},
                status=status.HTTP_202_ACCEPTED
            )

        if "group_id" in keys:
            group_to_remove = utils.group_from_id(request.query_params['group_id'])
            user_access.unshare_resource_with_group(resource,group_to_remove)
            return Response(
                data={'success': "Resource access privileges removed."},
                status=status.HTTP_202_ACCEPTED
            )

        return Response(
            data={'error': "Request must contain a 'resource' ID as well as a 'user' or 'group' id."},
            status=status.HTTP_200_OK
        )

        # def put(self, request, pk):
    #     pass
    #
