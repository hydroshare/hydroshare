from django.db.models import Q

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, UserResourcePrivilege, \
    GroupResourcePrivilege


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
    resource = BaseResource.objects.get(short_id=short_id)

    # public access
    if resource.raccess.public:
        privilege = [PrivilegeCodes.VIEW]
    else:
        privilege = [PrivilegeCodes.NONE]

    # user access
    privilege.extend(UserResourcePrivilege.objects.filter(
        user__email=email,
        resource__short_id=short_id).values_list('privilege', flat=True))

    # group access
    privilege.extend(GroupResourcePrivilege.objects.filter(
        Q(resource=resource,
          group__gaccess__active=True,
          group__g2ugp__user__email=email)).values_list('privilege', flat=True))

    return min(privilege)  # min of a list
