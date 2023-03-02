from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, Subquery

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, GroupResourcePrivilege


#############################################
# Shortcut queries for data access
# These queries shortcut around the typical assumptions of access control by
# taking in keys rather than objects and shortcutting around the whole process
# of resolving keys to objects, as used in the rest of access control.
# This saves oodles of time in processing requests from REST calls.
#############################################

def get_user_resource_privilege(email, short_id):
    # a naive solution with no performance enhancements:
    # These gets throw exceptions if no user or resource found or if duplicates exist.
    user = User.objects.get(email=email)
    resource = BaseResource.objects.get(short_id=short_id)
    # public access
    if resource.raccess.public:
        public = PrivilegeCodes.VIEW
    else:
        public = PrivilegeCodes.NONE
    # user access
    user_privilege = UserResourcePrivilege.get_privilege(user=user, resource=resource)

    group_privilege = GroupResourcePrivilege.objects.filter(
        Q(resource=resource,
          group__gaccess__active=True,
          group__g2ugp__user__email=email)).values_list('privilege', flat=True)
    print(group_privilege)
    if len(group_privilege) > 0:
        group_privilege = min(group_privilege)
    else:
        group_privilege = PrivilegeCodes.NONE

    print(group_privilege) 
    return min(public, user_privilege, group_privilege)
