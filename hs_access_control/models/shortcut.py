from django.db.models import Q
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view

from hs_access_control.models import ResourceAccess
from hs_access_control.models.privilege import PrivilegeCodes, UserResourcePrivilege, \
    GroupResourcePrivilege


#############################################
# Shortcut queries for data access
# These queries shortcut around the typical assumptions of access control by
# taking in keys rather than objects and shortcutting around the whole process
# of resolving keys to objects, as used in the rest of access control.
# This saves oodles of time in processing requests from REST calls.
#############################################


@api_view(['GET',])
def get_user_resource_privilege_endpoint(request, user_identifier, resource_id):
    privilege = get_user_resource_privilege(user_identifier, resource_id)
    return JsonResponse({"privilege": privilege}, status=status.HTTP_200_OK)


def get_user_resource_privilege(email, short_id):
    # return the privilege code 1-4 for a user and resource
    #
    # this never throws exceptions. It returns NONE:
    # - if a resource does not exist.
    # - if an email does not correspond to a user
    #
    # It returns the min of the privileges:
    # - if an email corresponds to more than one user account
    # - if a GUID somehow refers to more than one resource.

    # public access
    privilege = list(ResourceAccess.objects.filter(
        resource__short_id=short_id).values_list('public', flat='True'))

    if (len(privilege) > 0) and privilege[0]:  # boolean
        privilege = [PrivilegeCodes.VIEW]
    else:
        privilege = [PrivilegeCodes.NONE]

    # user access
    privilege.extend(UserResourcePrivilege.objects.filter(
        user__email=email,
        resource__short_id=short_id).values_list('privilege', flat=True))

    # group access
    privilege.extend(GroupResourcePrivilege.objects.filter(
        Q(resource__short_id=short_id,
          group__gaccess__active=True,
          group__g2ugp__user__email=email)).values_list('privilege', flat=True))

    if len(privilege) > 0:
        return min(privilege)  # min of a list
    else:
        return PrivilegeCodes.NONE
