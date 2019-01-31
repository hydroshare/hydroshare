from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserGroupPrivilege, UserResourcePrivilege, GroupResourcePrivilege, \
        GroupCommunityPrivilege

#############################################
# flags and methods for resources
#
# There is a one-to-one correspondence between instances of BaseResource and instances
# of ResourceAccess in order to annotate the BaseResource with flags and methods specific
# to access control.
#############################################


class ResourceAccess(models.Model):
    """ Resource model for access control
    """
    #############################################
    # model variables
    #############################################

    resource = models.OneToOneField(BaseResource,
                                    editable=False,
                                    null=False,
                                    related_name='raccess',
                                    related_query_name='raccess')

    # only for resources
    active = models.BooleanField(default=True,
                                 help_text='whether resource is currently active')
    # both resources and groups
    discoverable = models.BooleanField(default=False,
                                       help_text='whether resource is discoverable by everyone')
    public = models.BooleanField(default=False,
                                 help_text='whether resource data can be viewed by everyone')
    shareable = models.BooleanField(default=True,
                                    help_text='whether resource can be shared by non-owners')
    # these are for resources only
    published = models.BooleanField(default=False,
                                    help_text='whether resource has been published')
    immutable = models.BooleanField(default=False,
                                    help_text='whether to prevent all changes to the resource')

    require_download_agreement = models.BooleanField(default=False,
                                                     help_text='whether to require agreement to '
                                                               'resource rights statement for '
                                                               'resource content downloads')
    #############################################
    # workalike queries adapt to old access control system
    #############################################

    @property
    def view_users(self):
        """
        QuerySet of users with view privileges over a resource.

        This is a property so that it is a workalike for a prior explicit list.

        For VIEW, effective privilege = declared privilege, in the sense that all editors have
        VIEW, even if the resource is immutable.
        """

        return User.objects.filter(
            Q(is_active=True) &
            (Q(u2urp__resource=self.resource,  # direct privilege
               u2urp__privilege__lte=PrivilegeCodes.VIEW) |
             Q(u2ugp__group__gaccess__active=True,  # privilege through group
               u2ugp__group__g2grp__resource=self.resource,
               u2ugp__group__g2grp__privilege__lte=PrivilegeCodes.VIEW) |
             Q(u2ugp__group__gaccess__active=True,  # privilege through peer group
               u2ugp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
               u2ugp__group__g2gcp__community__c2gcp__group__g2grp__resource=self.resource)))\
            .distinct()

    @property
    def edit_users(self):
        """
        QuerySet of users with change privileges

        This is a property so that it is a workalike for a prior explicit list.

        If the resource is immutable, an empty QuerySet is returned.

        At present, this does not account for group/community behavior.
        """

        if self.immutable:
            return User.objects.none()
        else:
            return User.objects\
                       .filter(Q(is_active=True) &
                               (Q(u2urp__resource=self.resource,
                                  u2urp__privilege__lte=PrivilegeCodes.CHANGE) |
                                Q(u2ugp__group__gaccess__active=True,
                                  u2ugp__group__g2grp__resource=self.resource,
                                  u2ugp__group__g2grp__privilege__lte=PrivilegeCodes.CHANGE)))\
                .distinct()

    @property
    def view_groups(self):
        """
        QuerySet of groups with view privileges

        This is a property so that it is a workalike for a prior explicit list
        """
        return Group.objects.filter(
                Q(gaccess__active=True,
                  g2grp__resource=self.resource,
                  g2grp__privilege__lte=PrivilegeCodes.VIEW))

    @property
    def __all_view_groups(self):
        """
        QuerySet of groups with view privileges

        This is a property so that it is a workalike for a prior explicit list
        """
        return Group.objects.filter(
                Q(gaccess__active=True,
                  g2grp__resource=self.resource,
                  g2grp__privilege__lte=PrivilegeCodes.VIEW) |
                Q(gaccess__active=True,
                  g2gcp__community__c2gcp__allow_view=True,
                  g2gcp__community__c2gcp__group__gaccess__active=True,
                  g2gcp__community__c2gcp__group__g2grp__resource=self.resource)).distinct()

    @property
    def edit_groups(self):
        """
        QuerySet of groups with edit privileges

        This is a property so that it is a workalike for a prior explicit list.

        If the resource is immutable, an empty QuerySet is returned.

        Note that in terms of communities, edit for resources does not imply edit for groups.
        """
        if self.immutable:
            return Group.objects.none()
        else:
            return Group.objects.filter(gaccess__active=True,
                                        g2grp__resource=self.resource,
                                        g2grp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def owners(self):
        """
        QuerySet of users with owner privileges

        This is a property so that it is a workalike for a prior explicit list.

        For immutable resources, owners are not modified, but do not have CHANGE privilege.
        """
        return User.objects.filter(is_active=True,
                                   u2urp__privilege=PrivilegeCodes.OWNER,
                                   u2urp__resource=self.resource)

    def get_users_with_explicit_access(self, this_privilege, include_user_granted_access=True,
                                       include_group_granted_access=True):

        """
        Gets a QuerySet of Users who have the explicit specified privilege access to the resource.
        An empty list is returned if both include_user_granted_access and
        include_group_granted_access are set to False.

        :param this_privilege: the explict privilege over the resource for which list of users
         needed
        :param include_user_granted_access: if True, then users who have been granted directly the
        specified privilege will be included in the list
        :param include_group_granted_access: if True, then users who have been granted the
        specified privilege via group privilege over the resource will be included in the list
        :return:
        """
        # TODO: add communities
        if include_user_granted_access and include_group_granted_access:
            return User.objects.filter(Q(is_active=True) &
                                       (Q(u2urp__resource=self.resource,
                                          u2urp__privilege=this_privilege) |
                                        Q(u2ugp__group__g2grp__resource=self.resource,
                                          u2ugp__group__g2grp__privilege=this_privilege)))\
                               .distinct()
        elif include_user_granted_access:
            return User.objects.filter(Q(is_active=True) &
                                       (Q(u2urp__resource=self.resource,
                                          u2urp__privilege=this_privilege)))
        elif include_group_granted_access:
            return User.objects.filter(Q(is_active=True) &
                                       (Q(u2ugp__group__g2grp__resource=self.resource,
                                          u2ugp__group__g2grp__privilege=this_privilege)))\
                               .distinct()
        else:
            return User.objects.none()

    def __get_raw_user_privilege(self, this_user):
        """
        Return the user-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This does not account for resource flags.

        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        if this_user.is_superuser:
            return PrivilegeCodes.OWNER

        # compute simple user privilege over resource
        try:
            p = UserResourcePrivilege.objects.get(resource=self.resource,
                                                  user=this_user)
            response1 = p.privilege
        except UserResourcePrivilege.DoesNotExist:
            response1 = PrivilegeCodes.NONE

        return response1

    def __get_raw_group_privilege(self, this_user):
        """
        Return the group-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This does not account for resource flags.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        # Group privileges must be aggregated
        group_priv = GroupResourcePrivilege.objects\
            .filter(resource=self.resource,
                    group__gaccess__active=True,
                    group__g2ugp__user=this_user)\
            .aggregate(models.Min('privilege'))

        response2 = group_priv['privilege__min']
        if response2 is None:
            response2 = PrivilegeCodes.NONE
        return response2

    def __get_raw_community_privilege(self, this_user):
        """
        Return the community-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This does not account for resource flags.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        # privilege over communities of self
        # VIEW privilege arises from being a peer group of the group in a community
        group_view_priv = GroupResourcePrivilege.objects\
            .filter(Q(resource=self.resource,
                      group__gaccess__active=True,
                      group__g2gcp__community__c2gcp__allow_view=True,
                      group__g2gcp__community__c2gcp__group__gaccess__active=True,
                      group__g2gcp__community__c2gcp__group__g2ugp__user=this_user))\
            .aggregate(models.Min('privilege'))

        response2 = group_view_priv['privilege__min']
        if response2 is None:
            response2 = PrivilegeCodes.NONE

        # most permissive (lowest) privilege is effective.
        return response2

    def get_effective_user_privilege(self, this_user):
        """
        Return the effective user-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This accounts for resource flags by revoking CHANGE on immutable resources.
        """
        user_priv = self.__get_raw_user_privilege(this_user)
        if self.immutable and user_priv == PrivilegeCodes.CHANGE:
            return PrivilegeCodes.VIEW
        else:
            return user_priv

    def get_effective_group_privilege(self, this_user):
        """
        Return the effective group-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This accounts for resource flags by revoking CHANGE on immutable resources.
        """
        group_priv = self.__get_raw_group_privilege(this_user)
        if self.immutable and group_priv == PrivilegeCodes.CHANGE:
            return PrivilegeCodes.VIEW
        else:
            return group_priv

    def get_effective_community_privilege(self, this_user):
        """
        Return the effective community-based privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This accounts for resource flags by revoking CHANGE on immutable resources.
        """
        # at this point, this conditional does nothing, but there may
        # be cases in which this permission returns CHANGE in the future
        # TODO: include CHANGE chaining here
        group_priv = self.__get_raw_community_privilege(this_user)
        if self.immutable and group_priv == PrivilegeCodes.CHANGE:
            return PrivilegeCodes.VIEW
        else:
            return group_priv

    def get_effective_privilege(self, this_user):
        """
        Compute effective privilege of user over a resource, accounting for resource flags.

        :param this_user: user to check.
        :return: integer privilege 1-4

        This returns the effective privilege of a user over a resource, including both user
        and group privilege as well as resource flags. Return one of the PrivilegeCodes:

        This overrides stored privileges based upon two resource flags:

            * immutable:
                privilege is at most VIEW.

            * public:
                privilege is at least VIEW.

        Recall that *lower* privilege numbers indicate *higher* privilege.

        Usage
        -----

        This is not normally used in application code.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        user_priv = self.get_effective_user_privilege(this_user)
        group_priv = self.get_effective_group_privilege(this_user)
        community_priv = self.get_effective_community_privilege(this_user)
        return min(user_priv, group_priv, community_priv)

    @property
    def sharing_status(self):
        """ return the sharing status as a status word """
        if self.published:
            return "published"
        elif self.public:
            return "public"
        elif self.discoverable:
            return "discoverable"
        else:
            return "private"


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
    if UserGroupPrivilege.objects\
            .filter(user=u, group__g2gcp__community__c2gcp__group__g2grp__resource=r)\
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
                    group__g2gcp__community__c2gcp__allow_view=True,
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

# Map of possible privilege sources

# * direct resource privilege
#   User UserResourcePrivilege,
#         Resource

# * direct group privilege
#   User UserGroupPrivilege
#         (group=group) GroupResourcePrivilege
#         Resource

# * community privilege via a group
#   User UserGroupPrivilege
#         (group=group) GroupCommunityPrivilege  # privilege operative
#         (community=community) GroupCommunityPrivilege  # privilege NOT operative,
#                                                        # allow_view operative
#         (group=group) GroupResourcePrivilege  # privilege operative
#         Resource

# The minimal solution for communities requires some form of checking, some business model,
# and some way of listing resources available via a community.
# The appropriate pattern is;
# For communities to which the user belongs,
#    [uaccess.communities]
#    for groups within that community,
#        [community.get_groups_with_explicit_access(privilege)]
#        for resources in that group the user can change:
#            [group.get_resources_with_explicit_access(privilege=CHANGE)]
#            show resources
#        for resources in that group the user cannot change:
#            [group.get_resources_with_explicit_access(privilege=VIEW)]
#            show resources
