from django.contrib.auth.models import User
from django.db.models import Q, Subquery, OuterRef, Min
from django.db.models.functions import Coalesce, Least

from hs_access_control.models.privilege import UserResourcePrivilege, GroupResourcePrivilege, \
    UserGroupPrivilege, GroupCommunityPrivilege, PrivilegeCodes
from hs_core.models import BaseResource


def coarse_permissions(u, r):
    """ document the nature of permissions for resource r for user u """

    results = []
    # check raw user-resource privilege
    if UserResourcePrivilege.objects.filter(user=u, resource=r).exists():
        results.append("{} has user-resource privilege over '{}'"
                       .format(u.username, r.title))

    # check raw user-group privilege
    if UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r).exists():
        results.append("{} has user-group-resource privilege over '{}'"
                       .format(u.username, r.title))

    # check whether members of peer group can view community
    # we want to exclude cases where the peer group is self.
    if UserGroupPrivilege.objects\
            .filter(user=u, group__g2gcp__community__c2gcp__group__g2grp__resource=r)\
            .exclude(pk__in=UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r))\
            .exists():
        results.append("{} has user-group-community-group-resource privilege over '{}'"
                       .format(u.username, r.title))
    return results


def access_permissions(u, r):
    """ explain access for a specific user and resource """
    # verbs = ["undefined", "owns", "can edit", "can view", "cannot access"]
    results = list()

    # check raw user-resource privilege
    for q in UserResourcePrivilege.objects.filter(user=u, resource=r):
        # print("  * {} {} '{}'".format(u.username, verbs[q.privilege], r.title))
        results.append((q,))

    # check raw user-group-resource privilege
    for q in UserGroupPrivilege.objects.filter(user=u, group__g2grp__resource=r):
        for q2 in GroupResourcePrivilege.objects.filter(group=q.group, resource=r):
            results.append((q, q2,))

    # peer communities are given view privilege
    # This logic is complex. We want to prevent returns to the group from which we originated.
    # this will only happen if we start at a group with permission. So we prohibit that subcase
    # Check whether peers grant privilege by being in the same community
    for q in UserGroupPrivilege.objects\
            .filter(user=u,
                    group__gaccess__active=True,
                    group__g2gcp__community__c2gcp__group__gaccess__active=True,
                    group__g2gcp__community__c2gcp__group__g2grp__resource=r)\
            .exclude(pk__in=UserGroupPrivilege.objects.filter(user=u,
                                                              group__g2grp__resource=r)):
        for q2 in GroupCommunityPrivilege.objects.filter(
                group__gaccess__active=True,
                group=q.group,
                community__c2gcp__group__gaccess__active=True,
                community__c2gcp__group__g2grp__resource=r):
            for q3 in GroupCommunityPrivilege.objects.filter(
                    community=q2.community,
                    community__c2gcp__group__g2grp__resource=r):
                for q4 in GroupResourcePrivilege.objects\
                        .filter(group=q3.group, resource=r):
                    results.append((q, q2, q3, q4,))
    return results


def access_provenance(u, r):
    verbs = ["undefined", "owns", "can edit", "can view", "cannot access"]
    e = access_permissions(u, r)
    # pprint(e)
    output = "user {} {} resource '{}'\n"\
        .format(u.username, verbs[r.raccess.get_effective_privilege(u)], r.title)
    if r.raccess.immutable:
        output += "    '{}' is immutable: edit is replaced with view\n".format(r.title)
    for tuple in e:
        elements = list(tuple)
        found = False
        for e in elements:
            if isinstance(e, UserResourcePrivilege):
                output += "  * user {} {} resource.\n".format(e.user.username, verbs[e.privilege])
            elif isinstance(e, UserGroupPrivilege):
                output += "  * user {} {} group {},\n".format(e.user.username,
                                                              verbs[e.privilege],
                                                              e.group.name)
            elif isinstance(e, GroupResourcePrivilege):
                output += "    which {} resource.\n".format(verbs[e.privilege])
            elif isinstance(e, GroupCommunityPrivilege):
                if not found:
                    output += "    which {} community {},\n"\
                              .format(verbs[e.privilege], e.community.name)
                    found = True
                else:
                    output += "    which {} resources of group {},\n"\
                              .format(verbs[e.privilege], e.group.name)

    return output


def get_user_resource_privilege(user_id, short_id):
    """
    Determine the privilege level (permission) of a user for a specific resource.

    Args:
        user_id (int): The ID of the user.
        short_id (str): The unique identifier of the resource.

    Returns:
        int: The privilege code representing the user's access level.
    """

    if user_id is None:
        return PrivilegeCodes.NONE
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return PrivilegeCodes.NONE
    try:
        resource = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        return PrivilegeCodes.NONE

    # public access
    if resource.raccess.public or resource.raccess.allow_private_sharing:
        public = PrivilegeCodes.VIEW
    else:
        public = PrivilegeCodes.NONE
    # user access
    user_privilege = UserResourcePrivilege.get_privilege(user=user, resource=resource)

    group_privilege = GroupResourcePrivilege.objects.filter(
        Q(resource=resource,
          group__gaccess__active=True,
          group__g2ugp__user__id=user_id)).values_list('privilege', flat=True)

    if len(group_privilege) > 0:
        group_privilege = min(group_privilege)
    else:
        group_privilege = PrivilegeCodes.NONE

    return min(public, user_privilege, group_privilege)


def get_user_resources(user_id, owned=True, shared=True):
    """
    Get a list of resources that a user has access to, owned or shared, or both. Each resource is annotated with
    the user's effective privilege level as the 'user_permission' field.

    Args:
        user_id (int): The ID of the user.
        owned (bool): Whether to include only owned resources.
        shared (bool): Whether to include only shared resources (edit or view).

    Returns:
        list: A list of resources that the user has access to, owned or shared, or both.
    """
    if not owned and not shared:
        return BaseResource.objects.none()

    if user_id is None:
        return BaseResource.objects.none()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return BaseResource.objects.none()

    group_resources = GroupResourcePrivilege.objects.filter(
            group__g2ugp__user=user, group__gaccess__active=True).values_list('resource', flat=True)

    if owned and shared:
        user_resources = UserResourcePrivilege.objects.filter(user=user).values_list('resource', flat=True)
    elif shared:
        user_resources = UserResourcePrivilege.objects.filter(
            user=user,
            privilege__gt=PrivilegeCodes.OWNER
        )
        user_resources = user_resources.values_list('resource', flat=True)
    else:
        user_resources = UserResourcePrivilege.objects.filter(
            user=user,
            privilege=PrivilegeCodes.OWNER
        )
        user_resources = user_resources.values_list('resource', flat=True)
        group_resources = []

    resource_collection = BaseResource.objects.filter(Q(id__in=user_resources) | Q(id__in=group_resources))

    user_privilege_subquery = UserResourcePrivilege.objects.filter(
        user=user,
        resource=OuterRef('pk')
    ).values('privilege')

    group_privilege_subquery = GroupResourcePrivilege.objects.filter(
        resource=OuterRef('pk'),
        group__gaccess__active=True,
        group__g2ugp__user=user
    ).values('resource').annotate(min_priv=Min('privilege')).values('min_priv')

    # Annotates each resource (adding a new field 'user_permission') with the effective (the highest) privilege
    # level from user and group, defaulting to NONE (default should never happen).
    resource_collection = resource_collection.annotate(
        user_permission=Coalesce(
            Least(
                Coalesce(Subquery(user_privilege_subquery), PrivilegeCodes.NONE),
                Coalesce(Subquery(group_privilege_subquery), PrivilegeCodes.NONE)
            ),
            PrivilegeCodes.NONE
        )
    )
    resource_collection = resource_collection.filter(user_permission__lt=PrivilegeCodes.NONE)
    return resource_collection
