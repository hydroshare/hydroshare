from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, UserGroupPrivilege
from hs_access_control.models.community import Community

#############################################
# Group access data.
#
# GroupAccess has a one-to-one correspondence with the Group object
# and contains access control flags and methods specific to groups.
#
# To avoid UI difficulties, there has been an explicit decision not to modify
# the display routines for groups to display communities of groups.
# Rather, communities are exposed through a separate module community.py
# Only access-list functions have been modified for communities.
# * GroupAccess.view_resources and GroupAccess.edit_resources do reflect
#   community privileges, because they are used like access lists, while
# * GroupAccess.get_resources_with_explicit_access does *not* reflect
#   community privileges, because it is used to display a group's resources
#   on the group landing page. Including community resources would confuse this
#   depiction.
#############################################


class GroupMembershipRequest(models.Model):
    request_from = models.ForeignKey(User, related_name='ru2gmrequest')

    # when user is requesting to join a group this will be blank
    # when a group owner is sending an invitation, this field will represent the inviting user
    invitation_to = models.ForeignKey(User, null=True, blank=True, related_name='iu2gmrequest')
    group_to_join = models.ForeignKey(Group, related_name='g2gmrequest')
    date_requested = models.DateTimeField(editable=False, auto_now_add=True)


class GroupAccess(models.Model):
    """
    GroupAccess is in essence a group profile object
    Members are actually recorded in a separate model.
    Membership is equivalent with holding some privilege over the group.
    There is a well-defined notion of PrivilegeCodes.NONE for group,
    which to be a member with no privileges over the group, including
    even being able to view the member list. However, this is currently disallowed
    """

    # Django Group object: this has a side effect of creating Group.gaccess back relation.
    group = models.OneToOneField(Group,
                                 editable=False,
                                 null=False,
                                 related_name='gaccess',
                                 related_query_name='gaccess',
                                 help_text='group object that this object protects')

    active = models.BooleanField(default=True,
                                 editable=False,
                                 help_text='whether group is currently active')

    discoverable = models.BooleanField(default=True,
                                       editable=False,
                                       help_text='whether group description is discoverable' +
                                                 ' by everyone')

    public = models.BooleanField(default=True,
                                 editable=False,
                                 help_text='whether group members can be listed by everyone')

    shareable = models.BooleanField(default=True,
                                    editable=False,
                                    help_text='whether group can be shared by non-owners')

    auto_approve = models.BooleanField(default=False,
                                       editable=False,
                                       help_text='whether group membership can be auto approved')

    description = models.TextField(null=False, blank=False)
    purpose = models.TextField(null=True, blank=True)
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    picture = models.ImageField(upload_to='group', null=True, blank=True)

    ####################################
    # group membership: owners, edit_users, view_users are parallel to those in resources
    ####################################

    @property
    def owners(self):
        """
        Return list of owners for a group.

        :return: list of users

        Users can only own groups via direct links. Community-based ownership is not possible.
        """

        return User.objects.filter(is_active=True,
                                   u2ugp__group=self.group,
                                   u2ugp__privilege=PrivilegeCodes.OWNER)

    @property
    def __edit_users_of_group(self):
        """
        Q expression for users who can edit a group according to group privilege
        """
        return Q(is_active=True,
                 u2ugp__group=self.group,
                 u2ugp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def __edit_users_of_community(self):
        """
        Q expression for community members who can edit a group according to community privilege

        Only members of a supergroup (with CHANGE privilege) can edit individual groups.
        """
        return Q(is_active=True,
                 u2ugp__group__gaccess__active=True,
                 u2ugp__group__g2gcp__community__c2gcp__group=self.group,
                 u2ugp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE)

    @property
    def edit_users(self):
        """
        Return list of users who can add members to a group.

        :return: list of users

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(self.__edit_users_of_group)

    @property
    def __view_users_of_group(self):
        """
        Q expression for users who can view a group according to group privilege
        """
        return Q(is_active=True,
                 u2ugp__group=self.group,
                 u2ugp__privilege__lte=PrivilegeCodes.VIEW)

    @property
    def __view_users_of_community(self):
        """
        Q expression for community members who can view a group according to community privilege
        """
        return Q(is_active=True,
                 u2ugp__group__gaccess__active=True,
                 u2ugp__group__g2gcp__community__c2gcp__group=self.group)

    @property
    def view_users(self):
        """
        Return list of users who can add members to a group

        :return: list of users

        This eliminates duplicates due to multiple memberships, and includes community groups that
        have access, unlike members, which just lists explicit group members.
        """

        return User.objects.filter(self.__view_users_of_group)

    @property
    def members(self):
        """
        Return list of members for a group. This does not include communities.

        :return: list of users

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(is_active=True,
                                   u2ugp__group=self.group,
                                   u2ugp__privilege__lte=PrivilegeCodes.VIEW)

    @property
    def viewers(self):
        """ a viewer is not necessarily a member, due to community influence """
        return User.objects.filter(
                Q(is_active=True) &
                (Q(u2ugp__group__gaccess__active=True,
                   u2ugp__group=self.group) |
                 Q(u2ugp__group__gaccess__active=True,
                   u2ugp__group__g2gcp__allow_view=True,
                   u2ugp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
                   u2ugp__group__g2gcp__community__c2gcp__group=self.group))).distinct()

    def communities(self):
        """
        Return list of communities of which this group is a member.

        :return: list of communities

        """
        return Community.objects.filter(c2gcp__group=self.group)

    @property
    def __view_resources_of_group(self):
        """
        resources viewable according to group privileges

        Used in queries of BaseResource
        """
        return Q(r2grp__group=self.group)

    @property
    def __edit_resources_of_group(self):
        """
        resources editable according to group privileges

        Used in queries of BaseResource
        """
        return Q(r2grp__group=self.group,
                 raccess__immutable=False,
                 r2grp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def __view_resources_of_community(self):
        """
        Subquery Q expression for viewable resources according to community memberships

        Used in BaseResource queries only
        """
        return Q(r2grp__group__gaccess__active=True,
                 r2grp__group__g2gcp__allow_view=True,
                 r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.VIEW,
                 r2grp__group__g2gcp__community__c2gcp__group=self.group) |\
               Q(r2grp__group__gaccess__active=True,
                 r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
                 r2grp__group__g2gcp__community__c2gcp__group=self.group)

    @property
    def __edit_resources_of_community(self):
        """
        Subquery Q expression for editable resources according to community memberships

        Used in BaseResource queries only.
        """
        return Q(raccess__immutable=False,
                 r2grp__group__gaccess__active=True,
                 r2grp__privilege=PrivilegeCodes.CHANGE,
                 r2grp__group__g2gcp__community__c2gcp__group=self.group,
                 r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE)

    @property
    def view_resources(self):
        """
        QuerySet of resources held by group.

        :return: QuerySet of resource objects held by group.

        This includes directly accessible objects as well as objects accessible
        by nature of the fact that the current group is a member of a community
        containing another group that can access the object.

        """
        return BaseResource.objects.filter(self.__view_resources_of_group)

    @property
    def edit_resources(self):
        """
        QuerySet of resources that can be edited by group.

        :return: List of resource objects that can be edited by this group.

        These include resources that are directly editable, as well as those editable
        due to oversight privileges over a community
        """
        return BaseResource.objects.filter(self.__edit_resources_of_group)

    @property
    def group_membership_requests(self):
        """
        get a list of pending group membership requests for this group (self)
        :return: QuerySet
        """

        return GroupMembershipRequest.objects.filter(group_to_join=self.group,
                                                     group_to_join__gaccess__active=True)

    def get_resources_with_explicit_access(self, this_privilege):
        """
        Get a list of resources for which the group has the specified privilege

        :param this_privilege: one of the PrivilegeCodes
        :return: QuerySet of resource objects (QuerySet)

        This routine is an attempt to organize resources for displayability. It looks at the
        effective privilege rather than declared privilege, and squashes privilege that is in
        conflict with resource flags. If the resource is immutable, it is reported as a "VIEW"
        resource when the permission is "CHANGE", and as the original resource otherwise.
        """
        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        # this query computes resources with privilege X as follows:
        # a) There is a privilege of X for the object for group.
        # b) There is no lower privilege in either group privileges for the object.
        # c) Thus X is the effective privilege of the object.
        if this_privilege == PrivilegeCodes.OWNER:
            return BaseResource.objects.none()  # groups cannot own resources

        elif this_privilege == PrivilegeCodes.CHANGE:
            # CHANGE does not include immutable resources
            return BaseResource.objects.filter(raccess__immutable=False,
                                               r2grp__privilege=this_privilege,
                                               r2grp__group=self.group)
            # there are no excluded resources; maximum privilege is CHANGE

        else:  # this_privilege == PrivilegeCodes.VIEW
            # VIEW includes CHANGE & immutable as well as explicit VIEW
            return BaseResource.objects.filter(Q(r2grp__privilege=PrivilegeCodes.VIEW,
                                                 r2grp__group=self.group) |
                                               Q(raccess__immutable=True,
                                                 r2grp__privilege=PrivilegeCodes.CHANGE,
                                                 r2grp__group=self.group)).distinct()

    def get_users_with_explicit_access(self, this_privilege):
        """
        Get a list of users for which the group has the specified privilege

        :param this_privilege: one of the PrivilegeCodes
        :return: QuerySet of user objects (QuerySet)

        This does not account for community privileges. Just group privileges.
        """

        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if this_privilege == PrivilegeCodes.OWNER:
            return self.owners
        elif this_privilege == PrivilegeCodes.CHANGE:
            return User.objects.filter(is_active=True,
                                       u2ugp__group=self.group,
                                       u2ugp__privilege=PrivilegeCodes.CHANGE)
        else:  # this_privilege == PrivilegeCodes.VIEW
            return User.objects.filter(is_active=True,
                                       u2ugp__group=self.group,
                                       u2ugp__privilege=PrivilegeCodes.VIEW)

    def get_effective_privilege(self, this_user):
        """
        Return cumulative privilege for a user over a group

        :param this_user: User to check
        :return: Privilege code 1-4

        This does not account for community privileges. Just group privileges.
        """

        if not this_user.is_active:
            return PrivilegeCodes.NONE
        try:
            p = UserGroupPrivilege.objects.get(group=self.group,
                                               user=this_user)
            return p.privilege
        except UserGroupPrivilege.DoesNotExist:
            return PrivilegeCodes.NONE
