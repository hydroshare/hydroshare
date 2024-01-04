from django.db.models import Q

from django.contrib.auth.models import User
from hs_access_control.models.privilege import PrivilegeCodes, PrivilegeBase, \
    UserResourcePrivilege, GroupResourcePrivilege
from hs_access_control.models.exceptions import PolymorphismError
from hs_core.models import BaseResource
import hs_access_control.signals
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


#############################################
# Shortcut query for data access
# These queries shortcut around the typical assumptions of access control by
# taking in keys rather than objects and shortcutting around the whole process
# of resolving keys to objects, as used in the rest of access control.
# This saves oodles of time in processing requests from REST calls.
#############################################

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
    from hs_access_control.models import ResourceAccess

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


#############################################
# Zone of effect queries for the resources affected
# by a change in user access, group access, etc.
#############################################
# 1. Adding a user to a group: affects that user only, all resources
#    that the group can see.
# 2. Adding a user to a resource access list: affects that user/resource pair only.
# 3. Adding or removing a resource from a group: affects that resource
#    and all users in that group.
# 4. Making a resource public or private: affects potentially all users.
#    in other words, there's no situation in which a change affects
# both multiple users and multiple resources.
# this sends signal access_changed.

def zone_of_influence(send=True, **kwargs):
    for k in kwargs:
        print("{}: {}".format(k, kwargs[k]))
    if len(kwargs) > 2:
        raise PolymorphismError("Too many arguments")
    if len(kwargs) < 2:
        raise PolymorphismError("Too few arguments")
    if 'resource' in kwargs:
        if 'user' in kwargs:
            users = [kwargs['user'].username]
            resources = [kwargs['resource'].short_id]
        elif 'group' in kwargs:
            users = list(User.objects
                             .filter(u2ugp__group=kwargs['group'])
                             .values_list('username', flat=True))
            resources = [kwargs['resource'].short_id]
    elif 'user' in kwargs and 'group' in kwargs:
        users = [kwargs['user'].username]
        resources = list(BaseResource.objects
                                     .filter(r2grp__group=kwargs['group'])
                                     .values_list('short_id', flat=True))
    if send:
        hs_access_control.signals.access_changed.send(
            sender=PrivilegeBase, users=users, resources=resources)
    else:
        return (users, resources)


def zone_of_publicity(send=True, **kwargs):
    for k in kwargs:
        print("{}: {}".format(k, kwargs[k]))
    if len(kwargs) > 1:
        raise PolymorphismError("Too many arguments")
    if len(kwargs) < 1:
        raise PolymorphismError("Too few arguments")
    if 'resource' in kwargs:
        users = []
        resources = [kwargs['resource'].short_id]
    else:
        raise PolymorphismError("Invalid argument")
    if send:
        hs_access_control.signals.access_changed.send(
            sender=PrivilegeBase, users=users, resources=resources)
    else:
        return (users, resources)


@receiver(hs_access_control.signals.access_changed, sender=PrivilegeBase)
def access_changed(sender, **kwargs):
    print("access_changed: users: {} resources: {}".format(kwargs['users'], kwargs['resources']))
