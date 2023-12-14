from django.contrib.auth.models import Group
from rest_framework.exceptions import PermissionDenied
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
        return PrivilegeCodes.CHOICES[privilege - 1][1]


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
    Read, update, or delete access permission for a resource

    REST URL: hsapi/resource/{pk}/access
    HTTP method: GET
    :return: (on success): JSON representation of resource access with 'groups' and 'users' keys.

    REST URL: hsapi/resource/{pk}/access?(user_id=#|group_id=#)
    HTTP method: DELETE

    :type int
    :param user_id: user ID to remove
    :type int
    :param group_id: group ID to remove
    :return: (on success): Success or Error JSON object

    REST URL: hsapi/resource/{pk}/access
    HTTP method: PUT
    :return: (on success): Success or Error JSON object

    :type int
    :param user_id: user ID to remove
    :type int
    :param group_id: group ID to remove
    :type PrivilegeCode int
    :param privilege: PrivilegeCode to specifiy access level
    :return: (on success): Success or Error JSON objectit
    """

    serializer_class = UserResourcePrivilegeSerializer

    allowed_methods = ('GET', 'PUT', 'DELETE')

    def get(self, request, pk):
        view_utils.authorize(request, pk,
                             needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE_ACCESS)

        user_resource_serializer, group_resource_serializer = self.get_serializer_classes()
        user_resource_privilege, group_resource_privilege = self.get_queryset(pk, request.user)

        response_data = dict()
        response_data['users'] = \
            user_resource_serializer(user_resource_privilege, many=True).data
        response_data['groups'] = \
            group_resource_serializer(group_resource_privilege, many=True).data

        return Response(data=response_data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        view_utils.authorize(request, pk,
                             needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE_ACCESS)
        user_access = UserAccess(user=request.user)
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)
        keys = list(request.data.keys())

        if "user_id" in keys and "group_id" in keys:
            return Response(
                data={
                    'error': "Request cannot contain both a 'user_id' and a 'group_id' parameter."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if "user_id" in keys and "privilege" in keys:
            if int(request.data['privilege']) in (1, 2, 3, 4):
                try:
                    user_to_add = utils.user_from_id(request.data['user_id'])
                    user_access.share_resource_with_user(resource,
                                                         user_to_add,
                                                         int(request.data['privilege']))
                    return Response(
                        data={'success': "Resource access privileges added."},
                        status=status.HTTP_202_ACCEPTED
                    )
                except PermissionDenied as e:
                    return Response(
                        data={'error': f"This resource may not be shared with that user. {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        if "group_id" in keys and "privilege" in keys:
            if int(request.data['privilege']) in (1, 2, 3, 4):
                group_to_add = utils.group_from_id(request.data['group_id'])
                try:
                    user_access.share_resource_with_group(resource,
                                                          group_to_add,
                                                          int(request.data['privilege']))
                    return Response(
                        data={'success': "Resource access privileges added."},
                        status=status.HTTP_202_ACCEPTED
                    )
                except PermissionDenied as e:
                    return Response(
                        data={'error': f"This group may not be added to any resources. {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        message = "Request must contain a 'resource' ID as well as a 'user_id' or " \
                  "'group_id', and 'privilege' must be one of 1, 2, or 3."
        return Response(
            data={'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        view_utils.authorize(request, pk,
                             needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE_ACCESS)
        keys = list(request.query_params.keys())
        user_access = UserAccess(user=request.user)
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)

        if "user_id" in keys and "group_id" in keys:
            message = "Request cannot contain both a 'user_id' and a 'group_id' parameter."
            return Response(
                data={'error': message},
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
            user_access.unshare_resource_with_group(resource, group_to_remove)
            return Response(
                data={'success': "Resource access privileges removed."},
                status=status.HTTP_202_ACCEPTED
            )

        message = "Request must contain a 'resource' ID as well as a 'user_id' or 'group_id'"
        return Response(
            data={'error': message},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get_serializer_classes(self):
        return (UserResourcePrivilegeSerializer, GroupResourcePrivilegeSerializer,)

    def get_queryset(self, pk, user):
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)

        if user in resource.raccess.owners:
            querysets = (
                UserResourcePrivilege.objects.filter(resource=resource),
                GroupResourcePrivilege.objects.filter(resource=resource)
            )
        else:
            user_groups = Group.objects.filter(gaccess__g2ugp__user=user)
            querysets = (
                UserResourcePrivilege.objects.filter(resource=resource, user=user),
                GroupResourcePrivilege.objects.filter(resource=resource, group__in=user_groups)
            )

        return querysets
