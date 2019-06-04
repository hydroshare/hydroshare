from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q, Subquery
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserGroupPrivilege, UserResourcePrivilege, GroupResourcePrivilege, \
        UserCommunityPrivilege, GroupCommunityPrivilege
from hs_access_control.models.group import GroupAccess, GroupMembershipRequest
from hs_access_control.models.exceptions import PolymorphismError
from hs_access_control.models.community import Community

#############################################
# Methods and data for users
#
# There is a one-one correspondence between instances of UserAccess and instances of User.
# UserAccess annotates each user with information and methods necessary for access control.
#############################################


class UserAccess(models.Model):

    """
    UserAccess is in essence a part of the user profile object.
    We relate it to the native User model via the following cryptic code.
    This ensures that if we ever change our user model, this will adapt.
    This creates a back-relation User.uaccess to access this model.

    Here the methods that require user permission are kept.
    """

    user = models.OneToOneField(User,
                                editable=False,
                                null=False,
                                related_name='uaccess',
                                related_query_name='uaccess')

    ##########################################
    # PUBLIC METHODS: groups
    ##########################################

    def create_group_membership_request(self, this_group, this_user=None):
        """
        User request/invite to join a group
        :param this_group: group to join
        :param this_user: User invited to join a group,

        When user is requesting to join a group this_user is None,
        whereas when a group owner sends an invitation to a user to join,
        this_user is that user

        :return:

        For sending invitation for users to join a group, user self must be one of:

                * admin
                * group owner

        For sending a request to join a group, user self must be an active hydroshare user
        """

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if this_user and not this_user.is_active:
            raise PermissionDenied("Invited user is not active")

        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        if this_user is None:
            if self.user in this_group.gaccess.members:
                raise PermissionDenied("You are already a member of this group")
        elif this_user in this_group.gaccess.members:
                raise PermissionDenied("User is already a member of this group")

        # user (self) requesting to join a group
        if this_user is None:
            # check if the user already has made a request to join this_group
            if GroupMembershipRequest.objects.filter(request_from=self.user,
                                                     group_to_join=this_group).exists():
                raise PermissionDenied("You already have a pending request to join this group")
            else:
                membership_request = GroupMembershipRequest.objects.create(request_from=self.user,
                                                                           group_to_join=this_group)
                # if group allows auto approval of membership request then approve the
                # request immediately
                if this_group.gaccess.auto_approve:
                    # let first group owner be the grantor for this membership request
                    group_owner = this_group.gaccess.owners.order_by('u2ugp__start').first()
                    group_owner.uaccess.act_on_group_membership_request(membership_request)
                    membership_request = None
                return membership_request
        else:
            # group owner is inviting this_user to join this_group
            if not self.owns_group(this_group) and not self.user.is_superuser:
                raise PermissionDenied(
                    "You need to be a group owner to send invitation to join a group")

            if GroupMembershipRequest.objects.filter(group_to_join=this_group,
                                                     invitation_to=this_user).exists():
                raise PermissionDenied(
                    "You already have a pending invitation for this user to join this group")
            else:
                return GroupMembershipRequest.objects.create(request_from=self.user,
                                                             invitation_to=this_user,
                                                             group_to_join=this_group)

    def act_on_group_membership_request(self, this_request, accept_request=True):
        """
        group owner or user who received the invitation to act on membership request.
        Any group owner is allowed to accept/decline membership request made by any user who is not
        currently a member of the group. A user receiving an invitation from a group owner can
        either accept or decline to join a group.

        :param this_request: an instance of GroupMembershipRequest class
        :param accept_request: whether membership request to be accepted or declined/cancelled
        :return:

        User self must be one of:

                * admin
                * group owner
                * user who made the request (this_request)
        """

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        user_to_join_group = this_request.invitation_to if this_request.invitation_to \
            else this_request.request_from

        if not user_to_join_group.is_active:
            raise PermissionDenied("User to be granted group membership is not active")

        if not this_request.group_to_join.gaccess.active:
            raise PermissionDenied("Group is not active")

        membership_grantor = None
        # group owner acting on membership request from a user
        if this_request.invitation_to is None:
            if self.owns_group(this_request.group_to_join) or self.user.is_superuser:
                membership_grantor = self
            elif self.user == this_request.request_from and not accept_request:
                # allow self to cancel his own request to join a group
                pass
            else:
                raise PermissionDenied(
                    "You don't have permission to act on the group membership request")
        # invited user acting on membership invitation from a group owner
        elif this_request.invitation_to == self.user:
            membership_grantor = this_request.request_from.uaccess
            # owner may cancel his own invitation
        elif self.owns_group(this_request.group_to_join) or self.user.is_superuser:
                # allow this owner to cancel invitation generated by any group owner
                pass
        else:
            raise PermissionDenied(
                "You don't have permission to act on the group membership request")

        if accept_request and membership_grantor is not None:
            # user initially joins a group with 'VIEW' privilege
            membership_grantor.share_group_with_user(this_group=this_request.group_to_join,
                                                     this_user=user_to_join_group,
                                                     this_privilege=PrivilegeCodes.VIEW)
        this_request.delete()

    @property
    def group_membership_requests(self):
        """
        get a list of pending group membership requests/invitations for self
        :return: QuerySet
        """

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return GroupMembershipRequest.objects.filter(Q(request_from=self.user) |
                                                     Q(invitation_to=self.user))\
                                     .filter(group_to_join__gaccess__active=True)

    def create_group(self, title, description, auto_approve=False, purpose=None):
        """
        Create a group.

        :param title: Group title/name.
        :param description: a description of the group
        :param purpose: what's the purpose of the group (optional)
        :return: Group object

        Anyone can create a group. The creator is also the first owner.

        An owner can assign ownership to another user via share_group_with_user,
        but cannot remove self-ownership if that would leave the group with no
        owner.
        """
        if __debug__:
            assert isinstance(title, (str, unicode))
            assert isinstance(description, (str, unicode))
            if purpose:
                assert isinstance(purpose, (str, unicode))

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        raw_group = Group.objects.create(name=title)
        GroupAccess.objects.create(group=raw_group, description=description,
                                   auto_approve=auto_approve, purpose=purpose)
        raw_user = self.user

        # Must bootstrap access control system initially
        UserGroupPrivilege.share(group=raw_group,
                                 user=raw_user,
                                 grantor=raw_user,
                                 privilege=PrivilegeCodes.OWNER)
        return raw_group

    def delete_group(self, this_group):
        """
        Delete a group and all membership information.

        :param this_group: Group to delete.
        :return: None

        To delete a group a user must be owner or administrator.
        Deleting a group deletes all membership and sharing information.
        There is no undo.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser or self.owns_group(this_group):

            # THE FOLLOWING ARE UNNECESSARY due to delete cascade.
            # UserGroupPrivilege.objects.filter(group=this_group).delete()
            # GroupCommunityPrivilege.objects.filter(group=this_group).delete()
            # GroupResourcePrivilege.objects.filter(group=this_group).delete()
            # access_group.delete()

            this_group.delete()
        else:
            raise PermissionDenied("User must own group")

    ################################
    # held and owned groups
    ################################

    @property
    def view_groups(self):
        """
        Get a list of active groups accessible to self for view.

        Inactive groups will be included only if self owns those groups.

        :return: QuerySet evaluating to held groups.
        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return Group.objects.filter(Q(g2ugp__user=self.user,
                                      g2ugp__privilege__lte=PrivilegeCodes.VIEW,
                                      gaccess__active=True) |
                                    Q(g2ugp__user=self.user,
                                      gaccess__active=False,
                                      g2ugp__privilege=PrivilegeCodes.OWNER) |
                                    Q(gaccess__active=True,
                                      g2gcp__allow_view=True,
                                      g2gcp__community__c2gcp__group__gaccess__active=True,
                                      g2gcp__community__c2gcp__group__g2ugp__user=self.user) |
                                    Q(gaccess__active=True,
                                      g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
                                      g2gcp__community__c2gcp__group__gaccess__active=True,
                                      g2gcp__community__c2gcp__group__g2ugp__user=self.user))\
                            .distinct()

    @property
    def edit_groups(self):
        """
        Return a list of active groups editable by self.

        Inactive groups will be included only if self owns those groups.

        :return: QuerySet of groups editable by self.

        Usage:
        ------

        Because this returns a QuerySet, and not a set of objects, one can append
        extra QuerySet attributes to it, e.g. ordering, selection, projection:

            q = user.edit_groups
            q2 = q.order_by(...)
            v2 = q2.values('title')
            # etc

        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return Group.objects.filter(Q(g2ugp__user=self.user,
                                      g2ugp__privilege__lte=PrivilegeCodes.CHANGE,
                                      gaccess__active=True) |
                                    Q(g2ugp__user=self.user,
                                      gaccess__active=False,
                                      g2ugp__privilege=PrivilegeCodes.OWNER) |
                                    # edit privilege inherited from community
                                    Q(gaccess__active=True,
                                      g2gcp__community__c2gcp__group__gaccess__active=True,
                                      g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
                                      g2gcp__community__c2gcp__group__g2ugp__user=self.user))\
                            .distinct()

    @property
    def owned_groups(self):
        """
        Return a QuerySet of groups (includes inactive groups) owned by self.

        :return: QuerySet of groups owned by self.

        Usage:
        ------

        Because this returns a QuerySet, and not a set of objects, one can append
        extra QuerySet attributes to it, e.g. ordering, selection, projection:

            q = user.owned_groups
            q2 = q.order_by(...)
            v2 = q2.values('title')
            # etc

        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return Group.objects.filter(g2ugp__user=self.user,
                                    g2ugp__privilege=PrivilegeCodes.OWNER)

    #################################
    # access checks for groups
    #################################

    # There is a duality disparity between listing and access for groups.
    # The group interface requires owns_group, views_group, etc to concern
    # direct privilege. By contrast, the control functions can_*_group_*
    # must include indirect privilege. Thus the listing functions _all_*_groups
    # include indirect privilege

    @property
    def __all_view_groups(self):
        """
        Get a list of active groups accessible to self for view.

        Inactive groups will be included only if self owns those groups.

        :return: QuerySet evaluating to held groups.

        This returns all groups that are viewable, including owned groups and groups
        in communities to which the user has view access.
        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return Group.objects.filter(
                # owners can see inactive groups they own
                Q(g2ugp__user=self.user,
                  g2ugp__privilege=PrivilegeCodes.OWNER) |
                # everyone else can see only active groups they are in
                Q(gaccess__active=True,
                  g2ugp__user=self.user) |
                # if user has access to a group in a community, grant access to whole community
                Q(gaccess__active=True,
                  g2gcp__community__c2gcp__allow_view=True,
                  g2gcp__community__c2gcp__group__gaccess__active=True,
                  g2gcp__community__c2gcp__group__g2ugp__user=self.user) |
                # if the group's privilege over the community is CHANGE, override allow_view=False
                Q(gaccess__active=True,
                  g2gcp__privilege=PrivilegeCodes.CHANGE,
                  g2gcp__community__c2gcp__group__gaccess__active=True,
                  g2gcp__community__c2gcp__group__g2ugp__user=self.user)).distinct()

    def owns_group(self, this_group):
        """
        Boolean: is the user an owner of this group?

        :param this_group: group to check
        :return: Boolean: whether user is an owner.

        Usage:
        ------

            if my_user.owns_group(g):
                # do something that requires group ownership
                g.public=True
                g.discoverable=True
                g.save()
                my_user.unshare_user_with_group(g,another_user) # e.g.

        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return UserGroupPrivilege.objects.filter(group=this_group,
                                                 privilege=PrivilegeCodes.OWNER,
                                                 user=self.user).exists()

    def can_change_group(self, this_group):
        """
        Return whether a user can change this group, including the effect of resource flags.

        :param this_group: group to check
        :return: Boolean: whether user can change this group.

        For groups, ownership implies change privilege but not vice versa.
        Note that change privilege does not apply to group flags, including
        active, shareable, discoverable, and public. Only owners can set these.

        Usage:
        ------

            if my_user.can_change_group(g):
                # do something that requires change privilege with g.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        if self.user.is_superuser:
            return True

        return self.user in this_group.gaccess.edit_users

    def can_view_group(self, this_group):
        """
        Whether user can view this group in entirety

        :param this_group: group to check
        :return: True if user can view this resource.

        Usage:
        ------

            if my_user.can_view_group(g):
                # do something that requires viewing g.

        See can_view_metadata below for the special case of discoverable resources.

        Note that inferred viewers -- as determined by communities -- affect view privilege,
        and these can view groups of which they are a community.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser:
            return True

        if not this_group.gaccess.active and not self.owns_group(this_group):
            raise PermissionDenied("Group is not active")

        access_group = this_group.gaccess

        return self.user.is_superuser or access_group.public \
            or self.user in this_group.gaccess.view_users

    def can_view_group_metadata(self, this_group):
        """
        Whether user can view metadata (independent of viewing data).

        :param this_group: group to check
        :return: Boolean: whether user can view metadata

        For a group, metadata includes the group description and abstract, but not the
        member list. The member list is considered to be data.
        Being able to view metadata is a matter of being discoverable, public, or held.

        Usage:
        ------

            if my_user.can_view_metadata(some_group):
                # show metadata...
        """
        # allow access to non-logged in users for public or discoverable metadata.

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        return this_group.gaccess.discoverable or this_group.gaccess.public or \
               self.can_view_group(this_group)

    def can_change_group_flags(self, this_group):
        """
        Whether the current user can change group flags:

        :param this_group: group to query
        :return: True if the user can set flags.

        Usage:
        ------

            if my_user.can_change_group_flags(some_group):
                some_group.active=False
                some_group.save()

        In practice:
        ------------

        This routine is called *both* when building views and when writing responders.
        It should be called on both sides of the connection.

            * In a view builder, it determines whether buttons are shown for flag changes.

            * In a responder, it determines whether the request is valid.

        At this point, the return value is synonymous with ownership or admin.
        This may not always be true. So it is best to explicitly call this function
        rather than assuming implications between functions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_group(this_group)

    def can_delete_group(self, this_group):
        """
        Whether the current user can delete a group.

        :param this_group: group to query
        :return: True if the user can delete it.

        Usage:
        ------

            if my_user.can_delete_group(some_group):
                my_user.delete_group(some_group)
            else:
                raise PermissionDenied("Insufficient privilege")

        In practice:
        --------------

        At this point, this is synonymous with ownership or admin. This may not always be true.
        So it is best to explicitly call this function rather than assuming implications
        between functions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_group(this_group)

    # TODO: this should be split into
    #   can_share_group without optional arguments
    #   can_share_group_with_user
    #   can_share_community_with_group
    def can_share_group(self, this_group, this_privilege, user=None):
        """
        Return True if a given user can share this group with a given privilege.

        :param this_group: group to check
        :param this_privilege: privilege to assign
        :param user: user with which to share.
        :param community: group with which to share.
        :return: True if sharing is possible, otherwise false.

        This determines whether the current user can share a group, independent of
        what entity it might be shared with. An optional user parameter determines
        the target of the sharing.

        Usage:
        ------

            if my_user.can_share_group(some_group, PrivilegeCodes.VIEW, user=some_user):
                # ...time passes, forms are created, requests are made...
                my_user.share_group_with_user(some_group, some_user, PrivilegeCodes.VIEW)


        In practice:
        ------------

        If this returns False, UserAccess.share_group_with_user will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        # TODO: simplify this so that can_share_group_with_user calls can_share_group
        # TODO: and adds logic after that

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert this_privilege >= PrivilegeCodes.OWNER \
                and this_privilege <= PrivilegeCodes.VIEW
            if user is not None:
                assert isinstance(user, User)

        # TODO: these checks should not be caught by this routine
        # TODO: as they are caught above this level.
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")
        if user is not None:
            if not user.is_active:
                raise PermissionDenied("Grantee user is not active")

        try:
            self.__check_share_group(this_group, this_privilege, user=user)
            return True
        except PermissionDenied:
            return False

    # TODO: this needs to be split into
    #  __check_share_group without optional arguments
    #  __check_share_community_with_group
    #  __check_share_group_with_user
    def __check_share_group(self, this_group, this_privilege, user=None):

        """
        Raise exception if a given user cannot share this group with a given privilege.

        :param this_group: group to check
        :param this_privilege: privilege to assign
        :param user: (optional) user with which to share.
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a group, independent of
        what entity it might be shared with. An optional user parameter determines
        the target of the sharing.

        """
        access_group = this_group.gaccess

        # access control logic:
        # Can augment privilege if
        #   Admin
        #   Owner
        #   Permission for self
        #   Non-owner and shareable
        # Can downgrade privilege if
        #   Admin
        #   Owner
        #   Permission for self
        # cannot downgrade privilege just by having sharing privilege.

        grantor_priv = access_group.get_effective_privilege(self.user)
        if user is not None:
            grantee_priv = access_group.get_effective_privilege(user)
        else:
            grantee_priv = PrivilegeCodes.NONE

        # check for user authorization
        if self.user.is_superuser:
            pass  # admins can do anything

        elif grantor_priv == PrivilegeCodes.OWNER:
            pass  # owner can do anything

        elif access_group.shareable:
            if grantor_priv > PrivilegeCodes.VIEW:
                raise PermissionDenied("User has no privilege over group")

            if grantor_priv > this_privilege:
                raise PermissionDenied("User has insufficient privilege over group")

            if user is not None:
                # enforce non-idempotence for unprivileged users
                if grantee_priv == this_privilege:
                    raise PermissionDenied("Non-owners cannot reshare at existing privilege")

                if this_privilege > grantee_priv and user != self.user:
                    raise PermissionDenied("Non-owners cannot decrease privileges for others")

        else:
            raise PermissionDenied("User must own group or have sharing privilege")

        # regardless of privilege, cannot remove last owner
        if user is not None:
            if grantee_priv == PrivilegeCodes.OWNER \
                    and this_privilege != PrivilegeCodes.OWNER \
                    and access_group.owners.count() == 1:
                raise PermissionDenied("Cannot remove sole owner of group")

        return True

    ####################################
    # (can_)share_group_with_user: check for and implement share
    ####################################

    def can_share_group_with_user(self, this_group, this_user, this_privilege):
        """
        Return True if a given user can share this group with a specified user
        with a given privilege.

        :param self: requesting user
        :param this_group: group to check
        :param this_user: user to check
        :param this_privilege: privilege to assign to user
        :return: True if sharing is possible, otherwise false.

        This determines whether the current user can share a group with a specific user.

        Usage:
        ------

            if my_user.can_share_group_with_user(some_group, some_user, PrivilegeCodes.VIEW):
                # ...time passes, forms are created, requests are made...
                my_user.share_group_with_user(some_group, some_user, PrivilegeCodes.VIEW)

        In practice:
        ------------

        If this returns False, UserAccess.share_group_with_user will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        return self.can_share_group(this_group, this_privilege, user=this_user)

    def __check_share_group_with_user(self, this_group, this_user, this_privilege):
        """

        Raise exception if a given user cannot share this group with a given privilege
        to a specific user.

        :param this_group: group to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a group with a specific user.
        """
        return self.__check_share_group(this_group, this_privilege, user=this_user)

    def share_group_with_user(self, this_group, this_user, this_privilege):
        """
        :param this_group: Group to be affected.
        :param this_user: User with whom to share group
        :param this_privilege: privilege to assign: 1-4
        :return: none

        User self must be one of:

                * admin
                * group owner
                * group member with shareable=True

        and have equivalent or greater privilege over group.

        Usage:
        ------

            if my_user.can_share_group(some_group, PrivilegeCodes.CHANGE):
                # ...time passes, forms are created, requests are made...
                share_group_with_user(some_group, some_user, PrivilegeCodes.CHANGE)

        In practice:
        ------------

        "can_share_group" is used to construct views with appropriate buttons or popups,
        e.g., "share with...", while "share_group_with_user" is used in the form responder
        to implement changes.  This is safe to do even if the state changes, because
        "share_group_with_user" always rechecks permissions before implementing changes.
        If -- in the interim -- one removes my_user's sharing privileges, "share_group_with_user"
        will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        # raise a PermissionDenied exception if user self is not allowed to do this.
        self.__check_share_group_with_user(this_group, this_user, this_privilege)

        UserGroupPrivilege.share(group=this_group, user=this_user,
                                 grantor=self.user, privilege=this_privilege)

    ####################################
    # (can_)unshare_group_with_user: check for and implement unshare
    ####################################

    def unshare_group_with_user(self, this_group, this_user):
        """
        Remove a user from a group by removing privileges.

        :param this_group: Group to be affected.
        :param this_user: User with whom to unshare group
        :return: None

        This removes a user "this_user" from a group if "this_user" is not the sole owner and
        one of the following is true:
            * self is an administrator.
            * self owns the group.
            * this_user is self.

        Usage:
        ------

            if my_user.can_unshare_group_with_user(some_group, some_user):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_group_with_user(some_group, some_user)

        In practice:
        ------------

        "can_unshare_*" is used to construct views with appropriate forms and
        change buttons, while "unshare_*" is used to implement the responder to the
        view's forms. "unshare_*" still checks for permission (again) in case
        things have changed (e.g., through a stale form).
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        self.__check_unshare_group_with_user(this_group, this_user)
        UserGroupPrivilege.unshare(group=this_group, user=this_user, grantor=self.user)

    def can_unshare_group_with_user(self, this_group, this_user):
        """
        Determines whether a group can be unshared.

        :param this_group: group to be unshared.
        :param this_user: user to which to deny access.
        :return: Boolean: whether self can unshare this_group with this_user

        Usage:
        ------

            if my_user.can_unshare_group_with_user(some_group, some_user):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_group_with_user(some_group, some_user)

        In practice:
        ------------

        If this routine returns False, UserAccess.unshare_group_with_user is *guaranteed*
        to raise an exception.

-       Note that can_unshare_X is parallel to unshare_X and returns False exactly
-       when unshare_X will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)

        # these checks should not be caught by this routine
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        try:
            self.__check_unshare_group_with_user(this_group, this_user)
            return True
        except PermissionDenied:
            return False

    def __check_unshare_group_with_user(self, this_group, this_user):
        """ Check whether an unshare of a group with a user is permitted. """

        if this_user not in this_group.gaccess.members:
            raise PermissionDenied("User is not a member of the group")

        # Check for sufficient privilege
        if not self.user.is_superuser \
                and not self.owns_group(this_group) \
                and not this_user == self.user:
            raise PermissionDenied("You do not have permission to remove this sharing setting")

        # if this_user is not an OWNER, or there is another OWNER, OK.
        if not UserGroupPrivilege.objects.filter(group=this_group,
                                                 privilege=PrivilegeCodes.OWNER,
                                                 user=this_user).exists()\
            or UserGroupPrivilege.objects.filter(group=this_group,
                                                 privilege=PrivilegeCodes.OWNER) \
                                         .exclude(user=this_user).exists():
            return True
        else:
            raise PermissionDenied("Cannot remove sole owner of group")

    def get_group_unshare_users(self, this_group):
        """
        Get a QuerySet of users who could be unshared from this group.

        :param this_group: group to check.
        :return: QuerySet of users who could be removed by self.

        A user can be unshared with a group if:

            * The user is self
            * Self is group owner.
            * Self has admin privilege.

        except that a user in the QuerySet cannot be the last owner of the group.

        Usage:
        ------

            g = some_group
            u = some_user
            unshare_users = request_user.get_group_unshare_users(g)
            if u in unshare_users:
                self.unshare_group_with_user(g, u)
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser or self.owns_group(this_group):
            # everyone who holds this group, minus potential sole owners
            if access_group.owners.count() == 1:
                # get list of owners to exclude from main list
                # This should be one user but can be two due to race conditions.
                # Avoid races by excluding action in that case.
                users_to_exclude = User.objects.filter(is_active=True,
                                                       u2ugp__group=this_group,
                                                       u2ugp__privilege=PrivilegeCodes.OWNER)\
                                               .values('pk')
                return access_group.members.exclude(pk__in=Subquery(users_to_exclude))
            else:
                return access_group.members

        # unprivileged user can only remove grants to self, if any
        elif self.user in access_group.members:
            if access_group.owners.count() == 1:
                # if self is not an owner,
                if not UserGroupPrivilege.objects.filter(user=self.user,
                                                         group=this_group,
                                                         privilege=PrivilegeCodes.OWNER).exists():
                    # return a QuerySet containing only self
                    return User.objects.filter(uaccess=self)
                else:
                    # I can't unshare anyone
                    return User.objects.none()
            else:
                # I can unshare self as a non-owner.
                return User.objects.filter(uaccess=self)
        else:
            return User.objects.none()

    ####################################
    # get groups with specific access for a user
    ####################################

    # TODO: couch: check usage of this and expand to include community groups if possible
    def get_groups_with_explicit_access(self, this_privilege):
        """
        Get a QuerySet of groups for which the user has the specified privilege
        Args:
            this_privilege: one of the PrivilegeCodes

        Returns: QuerySet of group objects (QuerySet)
        """
        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        # this query computes groups with effective privilege X as follows:
        # a) There is a privilege of X for the object for user.
        # b) There is no lower privilege for the object.
        # c) Thus X is the effective privilege of the object.
        selected = Group.objects\
            .filter(g2ugp__user=self.user,
                    g2ugp__privilege=this_privilege)\
            .exclude(pk__in=Subquery(Group.objects.filter(g2ugp__user=self.user,
                                                          g2ugp__privilege__lt=this_privilege)
                                                  .values("pk")))

        # filter out inactive groups for non owner privileges
        if this_privilege != PrivilegeCodes.OWNER:
            selected.filter(gaccess__active=True)

        return selected

    ##########################################
    # PUBLIC METHODS: resources
    ##########################################

    @property
    def view_resources(self):
        """
        QuerySet of resources held by user.

        :return: QuerySet of resource objects accessible (in any form) to user.

        Held implies viewable. This includes group-community-group relationships,
        unlike GroupAccess.view_groups and GroupAccess.edit_groups.

        This can be subqueried in returns, because it is lazily evaluated.
        e.g., resource in self.uaccess.view_resources runs efficiently, because it
        is equivalent to self.uaccess.view_resources.filter(id=resource).exists()
        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return BaseResource.objects.filter(
            # direct access
            Q(r2urp__user=self.user) |
            # access via a group
            Q(r2grp__group__gaccess__active=True,
              r2grp__group__g2ugp__user=self.user) |
            # access via an unprivileged peer group in a community
            Q(r2grp__group__gaccess__active=True,
              r2grp__group__g2gcp__allow_view=True,
              r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
              r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user) |
            # access via a privileged peer group in a community
            Q(r2grp__group__gaccess__active=True,
              r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
              r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
              r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user)
            ).distinct()

    @property
    def owned_resources(self):
        """
        Get a QuerySet of resources owned by user.

        :return: List of resource objects owned by this user.

        This is simpler than view and edit access because groups can't own resources.
        """

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        return BaseResource.objects.filter(r2urp__user=self.user,
                                           r2urp__privilege=PrivilegeCodes.OWNER)

    @property
    def edit_resources(self):
        """
        Get a QuerySet of resources that can be edited by user.

        :return: QuerySet of resource objects that can be edited  by this user.

        This utilizes effective privilege; immutable resources are not returned.

        Note that this return includes all editable resources, whereas
        get_resources_with_explicit_access only returns those resources that are editable
        without being owned. Thus, this functions as an access list.
        """
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        # This is a mouthful.
        # a resource is editable if
        # 1. it's shared with the user and editable.
        # 2. it's shared with a group that has edit privilege and contains the user,
        # 3. it's shared with a group that has edit privilege and a community that
        #    contains the user, and the community share preserves edit

        return BaseResource.objects.filter(
            # user has direct access
            Q(raccess__immutable=False,
              r2urp__user=self.user,
              r2urp__privilege__lte=PrivilegeCodes.CHANGE) |
            # user has direct access through being a member of a group
            Q(raccess__immutable=False,
              r2grp__group__gaccess__active=True,
              r2grp__group__g2ugp__user=self.user,
              r2grp__privilege=PrivilegeCodes.CHANGE) |
            # user has access by being a member of a privileged group in the same community
            # Note: CHANGE privilege overrides allow_view flag.
            Q(raccess__immutable=False,
              r2grp__group__gaccess__active=True,
              r2grp__privilege=PrivilegeCodes.CHANGE,
              r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
              r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user,
              r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE))\
            .distinct()

    def get_resources_with_explicit_access(self, this_privilege,
                                           via_user=True, via_group=False, via_community=False):

        """
        Get a list of resources over which the user has the specified privilege

        :param this_privilege: A privilege code 1-3
        :param via_user: True to incorporate user privilege
        :param via_group: True to incorporate group privilege
        :param via_community: True to incorporate member group privileges

        Returns: list of resource objects (QuerySet)

        Note: One must check the immutable flag if privilege < VIEW.

        Note that in this computation,

        * Setting all of via_user, via_group, via_community to False is not an error, and
          always returns an empty QuerySet.
        * Via_group and via_community are meaningless for OWNER privilege and are ignored.
        * Exclusion clauses are meaningless for via_user as a user can have only one privilege.
        * The default is via_user=True, via_group=False, via_community=False, which is the original
          behavior of the routine before this revision.
        * Immutable resources are listed as VIEW even if the user or group has CHANGE
        * In the case of multiple privileges, the lowest privilege number
          (highest privilege) wins.

        However, please note that when via_user=True, via_group=True, via_community are True
        together, this applies to the **total combined privilege** rather than individual
        privileges. A detailed example:

        * Garfield shares group Cats with Sylvester as CHANGE
        * Garfield shares resource CatFood with Cats as CHANGE
          (Now Sylvester has CHANGE over CatFood)
        * Garfield shares resource CatFood with Sylvester as OWNER

        Then

            Sylvester.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE,
                                                                 via_user=True, via_group=True)

        **does not contain CatFood,** because Sylvester is an OWNER through user privilege,
        which "squashes" the group privilege, being higher.

        """
        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        incl = None  # what to include
        excl = None  # what to exclude

        if this_privilege == PrivilegeCodes.OWNER:
            if via_user:
                return BaseResource.objects\
                    .filter(r2urp__privilege=this_privilege,
                            r2urp__user=self.user)
            else:
                # groups and communities can't own resources
                return BaseResource.objects.none()

        # CHANGE does not include immutable resources
        elif this_privilege == PrivilegeCodes.CHANGE:

            # If something is immutable, CHANGE becomes VIEW
            if via_user:
                incl = Q(raccess__immutable=False,
                         r2urp__privilege=PrivilegeCodes.CHANGE,
                         r2urp__user=self.user)
                # exclude owners; immutability doesn't matter for them
                excl = Q(r2urp__privilege=PrivilegeCodes.OWNER,
                         r2urp__user=self.user)

            if via_group:
                gquery = Q(raccess__immutable=False,
                           r2grp__privilege=PrivilegeCodes.CHANGE,
                           r2grp__group__g2ugp__user=self.user)
                if incl is not None:
                    incl = incl | gquery
                else:
                    incl = gquery
                # CHANGE is highest permission; no need to exclude anything

            # community permission is CHANGE only if both permissions are CHANGE
            # allow_view does not apply to CHANGE access.
            if via_community:
                squery = Q(raccess__immutable=False,
                           r2grp__privilege=PrivilegeCodes.CHANGE,
                           r2grp__group__gaccess__active=True,
                           r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
                           r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user)
                if incl is not None:
                    incl = incl | squery
                else:
                    incl = squery
                # CHANGE is highest permission; no need to exclude anything

            if incl is not None:
                if excl:
                    # exclude owners; immutability doesn't matter for them
                    excluded = BaseResource.objects.filter(excl).values('pk')
                    return BaseResource.objects.filter(incl)\
                                               .exclude(pk__in=Subquery(excluded))\
                                               .distinct()
                else:
                    return BaseResource.objects.filter(incl).distinct()
            else:
                return BaseResource.objects.none()

        else:  # this_privilege == PrivilegeCodes.VIEW
            # VIEW includes CHANGE+immutable as well as explicit VIEW
            # CHANGE does not include immutable resources

            # pick up change and owner, use to override VIEW for groups
            if via_user:
                incl = \
                    Q(r2urp__privilege=PrivilegeCodes.VIEW,
                      r2urp__user=self.user) | \
                    Q(raccess__immutable=True,
                      r2urp__privilege=PrivilegeCodes.CHANGE,
                      r2urp__user=self.user)
                excl = Q(r2urp__privilege=PrivilegeCodes.OWNER,
                         r2urp__user=self.user)\

            if via_group:
                gquery = \
                    Q(r2grp__privilege=PrivilegeCodes.VIEW,
                      r2grp__group__g2ugp__user=self.user,
                      r2grp__group__gaccess__active=True) | \
                    Q(raccess__immutable=True,
                      r2grp__privilege=PrivilegeCodes.CHANGE,
                      r2grp__group__g2ugp__user=self.user,
                      r2grp__group__gaccess__active=True)
                if incl is not None:
                    incl = incl | gquery
                else:
                    incl = gquery
                # exclude groups with true CHANGE privilege
                gexcl = Q(raccess__immutable=False,
                          r2grp__privilege=PrivilegeCodes.CHANGE,
                          r2grp__group__g2ugp__user=self.user,
                          r2grp__group__gaccess__active=True)
                if excl is not None:
                    excl = excl | gexcl
                else:
                    excl = gexcl

            # community permission is VIEW if at least one of the two permissions is VIEW
            # or if the resource is immutable and there is any path to it.
            if via_community:
                cquery = \
                    Q(r2grp__group__gaccess__active=True,
                      r2grp__privilege=PrivilegeCodes.VIEW,  # overrides CHANGE in all cases
                      r2grp__group__g2gcp__community__c2gcp__allow_view=True,
                      r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
                      r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user) | \
                    Q(r2grp__group__gaccess__active=True,
                      r2grp__group__g2gcp__privilege=PrivilegeCodes.VIEW,  # not CHANGE
                      r2grp__group__g2gcp__community__c2gcp__allow_view=True,
                      r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
                      r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user) | \
                    Q(raccess__immutable=True,  # overrides even supervisor CHANGE
                      r2grp__group__gaccess__active=True,
                      r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
                      r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user)
                if incl is not None:
                    incl = incl | cquery
                else:
                    incl = cquery

                # exclude groups with true community CHANGE privilege
                cexcl = Q(raccess__immutable=False,
                          r2grp__privilege=PrivilegeCodes.CHANGE,
                          r2grp__group__gaccess__active=True,
                          r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.CHANGE,
                          r2grp__group__g2gcp__community__c2gcp__group__gaccess__active=True,
                          r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=self.user)
                if excl is not None:
                    excl = excl | cexcl
                else:
                    excl = cexcl

            if incl is not None:
                if excl:
                    # exclude higher privilege
                    excluded = BaseResource.objects.filter(r2urp__privilege=PrivilegeCodes.OWNER,
                                                           r2urp__user=self.user)\
                                                   .values('pk')

                    return BaseResource.objects.filter(incl)\
                                               .exclude(pk__in=Subquery(excluded))\
                                               .distinct()
                else:
                    return BaseResource.objects.filter(incl).distinct()
            else:
                return BaseResource.objects.none()

    #############################################
    # Check access permissions for self (user)
    #############################################

    def owns_resource(self, this_resource):
        """
        Boolean: is the user an owner of this resource?

        :param self: user on which to report.
        :return: True if user is an owner otherwise false

        Note that the fact that someone owns a resource is not sufficient proof that
        one has permission to change it, because resource flags can override the raw
        privilege. It is thus necessary to check that one can change something
        explicitly, using UserAccess.can_change_resource() amd/or
        UserAccess.can_change_resource_flags()
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return UserResourcePrivilege.objects.filter(resource=this_resource,
                                                    privilege=PrivilegeCodes.OWNER,
                                                    user=self.user).exists()

    def can_change_resource(self, this_resource):
        """
        Return whether a user can change this resource, including the effect of resource flags.

        :param self: User on which to report.
        :return: Boolean: whether user can change this resource.

        This result is advisory and is not enforced. The Django application must enforce this
        policy, using this routine for guidance.

        Note that

        * The ability to change a resource is not just contingent upon sharing,
          but also upon the resource flag "immutable". Thus "owns" does not imply
          "can change" privilege.
        * The ability to change a resource applies to its data and metadata, but not to its
          resource state flags: shareable, public, immutable, published, and discoverable.

        We elected not to return a queryset for this one, because that would mean that it
        would return two types depending upon conditions -- Boolean for simple queries and
        QuerySet for complex queries.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if self.user.is_superuser:
            return True

        if access_resource.immutable:
            return False

        if this_resource in self.edit_resources:
            return True

        return False

    def can_change_resource_flags(self, this_resource):
        """
        Whether self can change resource flags.

        :param this_resource: Resource to check.
        :return: True if user can set flags otherwise false.

        This is not enforced. It is up to the programmer to obey this restriction.

        This is not subject to immutability. Ar present, owns_resource -> can_change_resource_flags.
        If we made it subject to immutability, no resources could be made not immutable again.
        However, it should account for whether a resource is published, and return false if
        a resource is published.

        This is called from hs_core/views/authorize to authorize actions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or \
            (not this_resource.raccess.published and self.owns_resource(this_resource))

    def can_view_resource(self, this_resource):
        """
        Whether user can view this resource

        :param this_resource: Resource to check
        :return: True if user can view this resource, otherwise false.

        Note that:

        * One can view resources that are public, that one does not own.
        * Thus, this returns True for many public resources that are not returned from
          view_resources.
        * This is not sensitive to the setting for the "immutable" flag. That only affects editing.
        * This is called from hs_core/views/authorize to authorize actions.
        * This includes group-to-community, community-to-group, and community-to-group-to-community
          permissions

        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if access_resource.public or self.user.is_superuser:
            return True

        if this_resource in self.view_resources:
            return True

        return False

    def can_delete_resource(self, this_resource):
        """
        Whether user can delete a resource

        :param this_resource: Resource to check.
        :return: True if user can delete the resource, otherwise false.

        Note that

        * *Even immutable resources can be deleted.*
        * A resource must be published for deletion to be denied.
        * This is called from hs_core/views/authorize to authorize actions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser:
            return True

        return self.owns_resource(this_resource) and not this_resource.raccess.published

    ##########################################
    # check sharing rights
    ##########################################

    def can_share_resource(self, this_resource, this_privilege, user=None):
        """
        Can a resource be shared by the current user?

        :param this_resource: resource to check
        :param this_privilege: privilege to assign
        :param user: user to which privilege should be assigned (optional)
        :return: Boolean: whether resource can be shared.

        Several conditions require knowledge of the user with which the
        resource is to be shared.  These are handled optionally.

        This is called from hs_core/views/authorize to authorize actions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert this_privilege >= PrivilegeCodes.OWNER \
                and this_privilege <= PrivilegeCodes.VIEW
            if user is not None:
                assert isinstance(user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if user is not None and not user.is_active:
            raise PermissionDenied("Target user is not active")

        try:
            self.__check_share_resource(this_resource, this_privilege, user=user)
            return True
        except PermissionDenied:
            return False

    def __check_share_resource(self, this_resource, this_privilege, user=None):

        """
        Raise exception if a given user cannot share this resource with a given privilege.

        :param this_resource: resource to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a resource, independent of
        what entity it might be shared with. An optional user parameter determines
        the target of the sharing.

        This routine was changed on 12/13/2016 to avoid a detected anomaly.
        The "current privilege" of a user was previously that user's combined privilege
        granted as an individual and by groups. This caused an anomaly in which
        an individual could be made an OWNER of a group over which that user had CHANGE
        privilege, but could not be granted individual CHANGE privilege due to interference
        from the group privilege. This change makes that possible by separating the logic for
        group and user-level permissions.

        """
        # translate into ResourceAccess object
        access_resource = this_resource.raccess

        # access control logic:
        # Can augment privilege if
        #   Admin
        #   Owner
        #   Permission for self
        #   Non-owner and shareable
        # Can downgrade privilege if
        #   Admin
        #   Owner
        #   Permission for self
        # cannot downgrade privilege just by having sharing privilege.
        # also note the quota holder cannot be downgraded from owner privilege

        # grantor is assumed to have total privilege
        grantor_priv = access_resource.get_effective_privilege(self.user)
        # Target of sharing is considered to have only user privilege for these purposes
        # This makes user sharing independent of group sharing
        if user is not None:
            grantee_priv = access_resource.get_effective_user_privilege(user)

        # check for user authorization
        if self.user.is_superuser:
            pass  # admin can do anything

        elif grantor_priv == PrivilegeCodes.OWNER:
            pass  # owner can do anything

        elif access_resource.shareable:
            if grantor_priv > PrivilegeCodes.VIEW:
                raise PermissionDenied("User has no privilege over resource")

            if grantor_priv > this_privilege:
                raise PermissionDenied("User has insufficient privilege over resource")

            # Cannot check these without extra information that is optional
            if user is not None:
                # enforce non-idempotence for unprivileged users
                if grantee_priv == this_privilege:
                    raise PermissionDenied("Non-owners cannot reshare at existing privilege")
                if this_privilege > grantee_priv and user != self.user:
                    raise PermissionDenied("Non-owners cannot decrease privileges for others")

        else:
            raise PermissionDenied("User must own resource or have sharing privilege")

        # regardless of privilege, cannot remove last owner or quota holder
        if user is not None:
            if grantee_priv == PrivilegeCodes.OWNER and this_privilege != PrivilegeCodes.OWNER:
                if access_resource.owners.count() == 1:
                    raise PermissionDenied("Cannot remove sole owner of resource")
                qholder = this_resource.get_quota_holder()
                if qholder:
                    if qholder == user:
                        raise PermissionDenied("Cannot remove this resource's quota holder from "
                                               "ownership")

        return True

    def can_share_resource_with_user(self, this_resource, this_user, this_privilege):
        """
        Check whether one can share a resource with a user.

        :param this_resource: resource to share.
        :param this_user: user with which to share it.
        :param this_privilege: privilege level of sharing.
        :return: Boolean: whether one can share.

        This function returns False exactly when share_resource_with_group will raise
        an exception if called.
        """
        return self.can_share_resource(this_resource, this_privilege, user=this_user)

    def __check_share_resource_with_user(self, this_resource, this_user, this_privilege):
        """

        Raise exception if a given user cannot share this resource at a given privilege
        with a given user.

        :param this_resource: resource to check
        :param this_user: user to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a resource with
        a specific user.
        """
        return self.__check_share_resource(this_resource, this_privilege, user=this_user)

    def can_share_resource_with_group(self, this_resource, this_group, this_privilege):
        """
        Check whether one can share a resource with a group.

        :param this_resource: resource to share.
        :param this_group: group with which to share it.
        :param this_privilege: privilege level of sharing.
        :return: Boolean: whether one can share.

        This function returns False exactly when share_resource_with_group
        will raise an exception if called.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)
            assert this_privilege >= PrivilegeCodes.OWNER \
                and this_privilege <= PrivilegeCodes.VIEW

        access_group = this_group.gaccess

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not access_group.active:
            raise PermissionDenied("Group to share with is not active")

        try:
            self.__check_share_resource_with_group(this_resource, this_group, this_privilege)
            return True
        except PermissionDenied:
            return False

    def __check_share_resource_with_group(self, this_resource, this_group, this_privilege):
        """
        Raise exception if a given user cannot share this resource with a given group
        at a specific privilege.

        :param this_resource: resource to check
        :param this_group: group to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a resource with
        a specific group.
        """
        if this_privilege == PrivilegeCodes.OWNER:
            raise PermissionDenied("Groups cannot own resources")
        if this_privilege < PrivilegeCodes.OWNER or this_privilege > PrivilegeCodes.VIEW:
            raise PermissionDenied("Privilege level not valid")

        # check for user authorization
        if not self.can_share_resource(this_resource, this_privilege):
            raise PermissionDenied("User has insufficient sharing privilege over resource")

        # special exception for peer groups: CHANGE grants ability to share with community
        # without being member
        if not GroupCommunityPrivilege.objects.filter(
                privilege=PrivilegeCodes.CHANGE,
                community__c2gcp__group=this_group,
                group__g2ugp__user=self.user).exists() and\
           self.user not in this_group.gaccess.members and\
           not self.user.is_superuser:
            raise PermissionDenied("User is not a member of the group and not an admin")

        # At this point, the user is not an admin and an override has potentially been granted.
        # Treat this case as a regular group member trying to share something with the group.

        # enforce non-idempotence for unprivileged users
        try:
            current_priv = GroupResourcePrivilege.objects.get(group=this_group,
                                                              resource=this_resource).privilege
            if current_priv == this_privilege:
                raise PermissionDenied("Non-owners cannot reshare at existing privilege")

        except GroupResourcePrivilege.DoesNotExist:
            pass  # no problem if record does not exist

        return True

    #################################
    # share and unshare resources with user
    #################################

    def share_resource_with_user(self, this_resource, this_user, this_privilege):
        """
        Share a resource with a specific (third-party) user

        :param this_resource: Resource to be shared.
        :param this_user: User with whom to share resource
        :param this_privilege: privilege to assign: 1-4
        :return: none

        Assigning user (self) must be admin, owner, grantee, or have superior privilege over
        resource.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)
            assert isinstance(this_resource, BaseResource)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Target user is not active")

        # check that this is allowed and raise exception otherwise.
        self.__check_share_resource_with_user(this_resource, this_user, this_privilege)
        UserResourcePrivilege.share(resource=this_resource, user=this_user,
                                    grantor=self.user, privilege=this_privilege)

    def unshare_resource_with_user(self, this_resource, this_user):
        """
        Remove a user from a resource by removing privileges.

        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource

        This removes a user "this_user" from resource access to "this_resource" if one of
        the following is true:
            * self is an administrator.
            * self owns the group.
            * requesting user is the grantee of resource access.
        *and* removing the user will not lead to a resource without an owner.
        There is no provision for revoking lower-level permissions for an owner.
        If a user is a sole owner and holds other privileges, this call will not remove them.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Target user is not active")

        # check that this is allowed and raise exception otherwise.
        self.__check_unshare_resource_with_user(this_resource, this_user)
        UserResourcePrivilege.unshare(resource=this_resource, user=this_user,
                                      grantor=self.user)

    def can_unshare_resource_with_user(self, this_resource, this_user):

        """
        Check whether one can dissociate a specific user from a resource

        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether one can unshare this resource with this user.

        This checks if both of the following are true:
            * self is administrator, or owns the resource.
            * This act does not remove the last owner of the resource.
        If not, it returns False

-       Note that can_unshare_X is parallel to unshare_X and returns False exactly
-       when __check_unshare_X and unshare_X will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_user, User)

        # these checks should not be caught by this routine
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        try:
            self.__check_unshare_resource_with_user(this_resource, this_user)
            return True
        except PermissionDenied:
            return False

    def __check_unshare_resource_with_user(self, this_resource, this_user):
        """
        Check whether one can dissociate a specific user from a resource

        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether one can unshare this resource with this user.

        This checks if both of the following are true:
            * self is administrator, or owns the resource.
            * This act does not remove the last owner of the resource.
        If not, it raises a PermissionDenied exception.
        Otherwise, it returns True.

-       Note that can_unshare_X is parallel to unshare_X and returns False exactly
-       when __check_unshare_X and unshare_X will raise an exception.
        """
        if this_user not in this_resource.raccess.view_users:
            raise PermissionDenied("User does not have access to the group")

        # Check for sufficient privilege
        if not self.user.is_superuser \
                and not self.owns_resource(this_resource) \
                and not this_user == self.user:
            raise PermissionDenied("You do not have permission to remove this sharing setting")

        qholder = this_resource.get_quota_holder()
        if qholder:
            if qholder == this_user:
                raise PermissionDenied("Cannot remove this resource's quota holder from "
                                       "ownership")

        # if this_user is not an OWNER, or there is another OWNER, OK.
        if not UserResourcePrivilege.objects.filter(resource=this_resource,
                                                    privilege=PrivilegeCodes.OWNER,
                                                    user=this_user).exists()\
            or UserResourcePrivilege.objects.filter(resource=this_resource,
                                                    privilege=PrivilegeCodes.OWNER) \
                                            .exclude(user=this_user).exists():
            return True
        else:
            raise PermissionDenied("Cannot remove sole owner of group")

    ######################################
    # share and unshare resource with group
    ######################################

    def share_resource_with_group(self, this_resource, this_group, this_privilege):
        """
        Share a resource with a group

        :param this_resource: Resource to share.
        :param this_group: User with whom to share resource
        :param this_privilege: privilege to assign: 1-4
        :return: None

        Assigning user must be admin, owner, or have equivalent privilege over resource.
        Assigning user must be a member of the group.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)
            assert this_privilege >= PrivilegeCodes.OWNER \
                and this_privilege <= PrivilegeCodes.VIEW

        access_group = this_group.gaccess
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not access_group.active:
            raise PermissionDenied("Group to share with is not active")

        # validate the request as allowed
        self.__check_share_resource_with_group(this_resource, this_group, this_privilege)

        # User is authorized and privilege is appropriate;
        # proceed to change the record if present.
        GroupResourcePrivilege.share(resource=this_resource, group=this_group,
                                     grantor=self.user, privilege=this_privilege)

    def unshare_resource_with_group(self, this_resource, this_group):
        """
        Remove a group from access to a resource by removing privileges.

        :param this_resource: resource to be affected.
        :param this_group: user with which to unshare resource
        :return: None

        This removes a user "this_group" from access to "this_resource" if one of the
        following is true:
            * self is an administrator.
            * self owns the resource.
            * self owns the group.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        # check that this is allowed
        self.__check_unshare_resource_with_group(this_resource, this_group)
        GroupResourcePrivilege.unshare(resource=this_resource, group=this_group, grantor=self.user)

    def can_unshare_resource_with_group(self, this_resource, this_group):
        """
        Check whether one can unshare a resource with a group.

        :param this_resource: resource to be protected.
        :param this_group: group with which to unshare resource.
        :return: Boolean

        Unsharing will remove a user "this_group" from access to "this_resource" if one of the
        following is true:
            * self is an administrator.
            * self owns the resource.
            * self owns the group.
        This routine returns False exactly when unshare_resource_with_group will raise a
        PermissionDenied exception.

-       Note that can_unshare_X is parallel to unshare_X and returns False exactly
-       when unshare_X will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)

        # these checks should not be caught by this routine
        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        try:
            self.__check_unshare_resource_with_group(this_resource, this_group)
            return True
        except PermissionDenied:
            return False

    def __check_unshare_resource_with_group(self, this_resource, this_group):
        """ check that one can unshare a group with a resource, raise PermissionDenied if not """
        if not (this_group in this_resource.raccess.view_groups):
            raise PermissionDenied("Group does not have access to resource")

        # TODO: also authorize owners of the group and members of peer groups in communities
        # Check for sufficient privilege
        if not self.user.is_superuser \
                and not self.owns_resource(this_resource):
            raise PermissionDenied("Insufficient privilege to unshare resource")
        return True

    def get_resource_unshare_users(self, this_resource):
        """
        Get a list of users who could be unshared from this resource.

        :param this_resource: resource to check.
        :return: list of users who could be removed by self.

        Users who can be removed fall into three catagories

        a) self is admin: everyone.
        b) self is resource owner: everyone except resource's quota holder.
        c) self is beneficiary: self only
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess
        qholder = this_resource.get_quota_holder()
        if self.user.is_superuser or self.owns_resource(this_resource):
            # everyone who holds this resource, minus potential sole owners
            if access_resource.owners.count() == 1:
                # get list of owners to exclude from main list
                # This should be one user but can be two due to race conditions.
                # Avoid races by excluding whole action in that case.
                users_to_exclude = User.objects.filter(is_active=True,
                                                       u2urp__resource=this_resource,
                                                       u2urp__privilege=PrivilegeCodes.OWNER)\
                                               .values('pk')
                return access_resource.view_users.exclude(pk__in=Subquery(users_to_exclude))
            elif qholder:
                return access_resource.view_users.exclude(id=qholder.id)
            else:
                return access_resource.view_users

        # unprivileged user can only remove grants to self, if any
        elif self.user in access_resource.view_users:
            if access_resource.owners.count() == 1:
                # if self is not an owner,
                if not UserResourcePrivilege.objects\
                        .filter(user=self.user,
                                resource=this_resource,
                                privilege=PrivilegeCodes.OWNER)\
                        .exists():
                    # return a QuerySet containing only self
                    return User.objects.filter(uaccess=self)
                else:
                    # I can't unshare anyone
                    return User.objects.none()
            else:
                # I can unshare self even as an owner.
                return User.objects.filter(uaccess=self)
        else:
            return User.objects.none()

    def get_resource_unshare_groups(self, this_resource):
        """
        Get a list of groups who could be unshared from this resource.

        :param this_resource: resource to check.
        :return: list of groups who could be removed by self.

        This is a list of groups for which unshare_resource_with_group will work for this user.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        # Users who can be removed fall into three categories
        # a) self is admin: everyone with access.
        # b) self is resource owner: everyone with access.
        # c) self is group owner: only for owned groups

        if self.user.is_superuser or self.owns_resource(this_resource):
            # all shared groups
            return Group.objects.filter(g2grp__resource=this_resource, gaccess__active=True)
        else:
            return Group.objects.filter(g2ugp__user=self.user,
                                        g2ugp__privilege=PrivilegeCodes.OWNER,
                                        gaccess__active=True)

    #######################
    # "undo" system based upon provenance
    #######################

    def __get_group_undo_users(self, this_group):
        """
        Get a list of users whose privilege was granted by self and can be undone.

        :param this_group: group to check.
        :returns: QuerySet of users

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, one can undo a share that one no longer has the privilege to grant.

        This excludes single owners from the list of undo users to avoid removing last owner.

        Usage:
        ------

            g = some_group
            u = some_user
            if request_user.can_undo_share_group_with_user(g,u)
                request_user.undo_share_group_with_user(g,u)

        """
        if __debug__:
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        candidates = UserGroupPrivilege.get_undo_users(group=this_group, grantor=self.user)
        # figure out if group has a single owner
        if this_group.gaccess.owners.count() == 1:
            # get list of owners to exclude from main list
            users_to_exclude = User.objects.filter(is_active=True,
                                                   u2ugp__group=this_group,
                                                   u2ugp__privilege=PrivilegeCodes.OWNER)\
                                           .values('pk')
            return candidates.exclude(pk__in=Subquery(users_to_exclude))
        else:
            return candidates

    def can_undo_share_group_with_user(self, this_group, this_user):
        """
        Check that a group share can be undone

        :param this_group: group to check.
        :param this_user: user to check.
        :returns: Boolean

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus -- under freakish circumstances --  one can undo a share that one no
        longer has the privilege to grant.

        Usage:
        ------

            g = some_group
            u = some_user
            if request_user.can_undo_share_group_with_user(g,u)
                request_user.undo_share_group_with_user(g,u)
        """
        if __debug__:
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")
        if not this_user.is_active:
            raise PermissionDenied("User is not active")

        return this_user in self.__get_group_undo_users(this_group)

    def undo_share_group_with_user(self, this_group, this_user):
        """
        Undo a share with a user that was granted by self

        :param this_group: group for which to remove privilege.
        :param this_user: user to remove from privilege.

        This routine undoes a privilege previously granted by self.  Only the last granted
        privilege for a group can be undone.  If some other user has granted a new (greater)
        privilege, then the new privilege cannot be undone by the original user.

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        Usage:
        ------

            g = some_group
            u = some_user
            if request_user.can_undo_share_group_with_user(g, u)
                request_user.undo_share_group_with_user(g, u)
        """

        if __debug__:
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")
        if not this_user.is_active:
            raise PermissionDenied("User is not active")

        qual_undo = self.__get_group_undo_users(this_group)
        if this_user in qual_undo:
            UserGroupPrivilege.undo_share(group=this_group, user=this_user, grantor=self.user)
        else:
            # determine which exception to raise.
            raw_undo = UserGroupPrivilege.get_undo_users(group=this_group, grantor=self.user)
            if this_user in raw_undo:
                raise PermissionDenied("Cannot remove last owner of group")
            else:
                raise PermissionDenied("User did not grant last privilege")

    ##################################
    # undo for resources
    ##################################

    def __get_resource_undo_users(self, this_resource):
        """
        Get a list of users whose privilege was granted by self and can be undone.

        :param this_resource: resource to check.
        :returns: QuerySet of users

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        This excludes single owners from the list of undo users to avoid removing last owner.

        Usage:
        ------

            g = some_resource
            u = some_user
            if request_user.can_undo_share_resource_with_user(g,u)
                request_user.undo_share_resource_with_user(g,u)

        """
        if __debug__:
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        candidates = UserResourcePrivilege.get_undo_users(resource=this_resource, grantor=self.user)
        # figure out if group has a single owner
        if this_resource.raccess.owners.count() == 1:
            # get list of owners to exclude from main list
            users_to_exclude = User.objects.filter(is_active=True,
                                                   u2urp__resource=this_resource,
                                                   u2urp__privilege=PrivilegeCodes.OWNER)\
                                           .values('pk')
            return candidates.exclude(pk__in=Subquery(users_to_exclude))
        else:
            return candidates

    def can_undo_share_resource_with_user(self, this_resource, this_user):
        """ Check that a resource share can be undone """
        if __debug__:
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("User is not active")

        return this_user in self.__get_resource_undo_users(this_resource)

    def undo_share_resource_with_user(self, this_resource, this_user):
        """
        Undo a share with a user that was granted by self.

        :param this_resource: resource for which to remove privilege.
        :param this_user: user to remove from privilege.

        This routine undoes a privilege previously granted by self.  Only the last granted
        privilege for a resource can be undone.  If some other user has granted a new (greater)
        privilege, then the new privilege cannot be undone by the original user.

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        Usage:
        ------

            r = some_resource
            u = some_user
            if request_user.can_undo_share_resource_with_user(r, u)
                request_user.undo_share_resource_with_user(r, u)
        """

        if __debug__:
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("User is not active")

        qual_undo = self.__get_resource_undo_users(this_resource)
        if this_user in qual_undo:
            UserResourcePrivilege.undo_share(resource=this_resource,
                                             user=this_user,
                                             grantor=self.user)
        else:
            # determine which exception to raise.
            raw_undo = UserResourcePrivilege.get_undo_users(resource=this_resource,
                                                            grantor=self.user)
            if this_user in raw_undo:
                raise PermissionDenied("Cannot remove last owner of resource")
            else:
                raise PermissionDenied("User did not grant last privilege")

    def __get_resource_undo_groups(self, this_resource):
        """ get a list of groups that can be removed from resource privilege by self """
        """
        Get a list of users whose privilege was granted by self and can be undone.

        :param this_resource: resource to check.
        :returns: QuerySet of users

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        This excludes single owners from the list of undo users to avoid removing last owner.

        Usage:
        ------

            r = some_resource
            g = some_group
            undo_groups = request_user.__get_resource_undo_groups(r)
            if u in undo_groups:
                request_user.undo_share_resource_with_group(r,g)

        """
        if __debug__:
            assert isinstance(this_resource, BaseResource)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return GroupResourcePrivilege.get_undo_groups(resource=this_resource, grantor=self.user)

    def can_undo_share_resource_with_group(self, this_resource, this_group):
        """ Check that a resource share can be undone """
        if __debug__:
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        return this_group in self.__get_resource_undo_groups(this_resource)

    def undo_share_resource_with_group(self, this_resource, this_group):
        """
        Undo a share with a group that was granted by self.

        :param this_resource: resource for which to remove privilege.
        :param this_group: group to remove from privilege.

        This routine undoes a privilege previously granted by self.  Only the last granted
        privilege for a resource can be undone.  If some other user has granted a new (greater)
        privilege, then the new privilege cannot be undone by the original user.

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        Usage:
        ------

            r = some_resource
            g = some_group
            if request_user.can_undo_share_resource_with_group(r, g):
                request_user.undo_share_resource_with_group(r, g)
        """

        if __debug__:
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        qual_undo = self.__get_resource_undo_groups(this_resource)
        if this_group in qual_undo:
            GroupResourcePrivilege.undo_share(resource=this_resource,
                                              group=this_group,
                                              grantor=self.user)
        else:
            raise PermissionDenied("User did not grant last privilege")

    #######################
    # polymorphic functions understand variable arguments for main functions
    #######################

    def share(self, **kwargs):
        if __debug__:
            assert len(kwargs) == 3
            assert 'privilege' in kwargs and \
                kwargs['privilege'] >= PrivilegeCodes.OWNER and \
                kwargs['privilege'] <= PrivilegeCodes.NONE
            assert 'resource' not in kwargs or isinstance(kwargs['resource'], BaseResource)
            assert 'group' not in kwargs or isinstance(kwargs['group'], Group)
            assert 'user' not in kwargs or isinstance(kwargs['user'], User)
            assert 'community' not in kwargs or isinstance(kwargs['community'], Community)
        if 'resource' in kwargs and 'user' in kwargs:
            return self.share_resource_with_user(kwargs['resource'], kwargs['user'],
                                                 kwargs['privilege'])
        elif 'resource' in kwargs and 'group' in kwargs:
            return self.share_resource_with_group(kwargs['resource'], kwargs['group'],
                                                  kwargs['privilege'])
        elif 'group' in kwargs and 'user' in kwargs:
            return self.share_group_with_user(kwargs['group'], kwargs['user'],
                                              kwargs['privilege'])
        elif 'group' in kwargs and 'community' in kwargs:
            return self.share_community_with_group(kwargs['group'], kwargs['community'],
                                                   kwargs['privilege'])
        elif 'user' in kwargs and 'community' in kwargs:
            return self.share_user_with_community(kwargs['user'], kwargs['community'],
                                                  kwargs['privilege'])
        else:
            raise PolymorphismError(str.format("No action for arguments {}", str(kwargs)))

    def unshare(self, **kwargs):
        if __debug__:
            assert len(kwargs) == 2
            assert 'resource' not in kwargs or isinstance(kwargs['resource'], BaseResource)
            assert 'group' not in kwargs or isinstance(kwargs['group'], Group)
            assert 'user' not in kwargs or isinstance(kwargs['user'], User)
        if 'resource' in kwargs and 'user' in kwargs:
            return self.unshare_resource_with_user(kwargs['resource'], kwargs['user'])
        elif 'resource' in kwargs and 'group' in kwargs:
            return self.unshare_resource_with_group(kwargs['resource'], kwargs['group'])
        elif 'group' in kwargs and 'user' in kwargs:
            return self.unshare_group_with_user(kwargs['group'], kwargs['user'])
        elif 'group' in kwargs and 'community' in kwargs:
            return self.unshare_community_with_group(kwargs['group'], kwargs['community'])
        elif 'user' in kwargs and 'community' in kwargs:
            return self.unshare_user_with_community(kwargs['user'], kwargs['community'])
        else:
            raise PolymorphismError(str.format("No action for arguments {}", str(kwargs)))

    def can_unshare(self, **kwargs):
        if __debug__:
            assert len(kwargs) == 2
            assert 'resource' not in kwargs or isinstance(kwargs['resource'], BaseResource)
            assert 'group' not in kwargs or isinstance(kwargs['group'], Group)
            assert 'user' not in kwargs or isinstance(kwargs['user'], User)
        if 'resource' in kwargs and 'user' in kwargs:
            return self.can_unshare_resource_with_user(kwargs['resource'], kwargs['user'])
        elif 'resource' in kwargs and 'group' in kwargs:
            return self.can_unshare_resource_with_group(kwargs['resource'], kwargs['group'])
        elif 'group' in kwargs and 'user' in kwargs:
            return self.can_unshare_group_with_user(kwargs['group'], kwargs['user'])
        elif 'group' in kwargs and 'community' in kwargs:
            return self.can_unshare_community_with_group(kwargs['group'], kwargs['community'])
        elif 'user' in kwargs and 'community' in kwargs:
            return self.can_unshare_user_with_community(kwargs['user'], kwargs['community'])
        else:
            raise PolymorphismError(str.format("No action for arguments {}", str(kwargs)))

    def undo_share(self, **kwargs):
        if __debug__:
            assert len(kwargs) == 2
            assert 'resource' not in kwargs or isinstance(kwargs['resource'], BaseResource)
            assert 'group' not in kwargs or isinstance(kwargs['group'], Group)
            assert 'user' not in kwargs or isinstance(kwargs['user'], User)
        if 'resource' in kwargs and 'user' in kwargs:
            return self.undo_share_resource_with_user(kwargs['resource'], kwargs['user'])
        elif 'resource' in kwargs and 'group' in kwargs:
            return self.undo_share_resource_with_group(kwargs['resource'], kwargs['group'])
        elif 'group' in kwargs and 'user' in kwargs:
            return self.undo_share_group_with_user(kwargs['group'], kwargs['user'])
        elif 'group' in kwargs and 'community' in kwargs:
            return self.undo_share_community_with_group(kwargs['group'], kwargs['community'])
        elif 'user' in kwargs and 'community' in kwargs:
            return self.undo_share_user_with_community(kwargs['user'], kwargs['community'])
        else:
            raise PolymorphismError(str.format("No action for arguments {}", str(kwargs)))

    def can_undo_share(self, **kwargs):
        if __debug__:
            assert len(kwargs) == 2
            assert 'resource' not in kwargs or isinstance(kwargs['resource'], BaseResource)
            assert 'group' not in kwargs or isinstance(kwargs['group'], Group)
            assert 'user' not in kwargs or isinstance(kwargs['user'], User)

        if 'resource' in kwargs and 'user' in kwargs:
            return self.can_undo_share_resource_with_user(kwargs['resource'], kwargs['user'])
        elif 'resource' in kwargs and 'group' in kwargs:
            return self.can_undo_share_resource_with_group(kwargs['resource'], kwargs['group'])
        elif 'group' in kwargs and 'user' in kwargs:
            return self.can_undo_share_group_with_user(kwargs['group'], kwargs['user'])
        elif 'group' in kwargs and 'community' in kwargs:
            return self.can_undo_share_community_with_group(kwargs['group'], kwargs['community'])
        elif 'user' in kwargs and 'community' in kwargs:
            return self.can_undo_share_user_with_community(kwargs['user'], kwargs['community'])
        else:
            raise PolymorphismError(str.format("No action for arguments {}", str(kwargs)))

    ##########################################
    # PUBLIC METHODS: community
    ##########################################

    def create_community(self, title, description, auto_approve=False, purpose=None):
        """
        Create a community.

        :param title: Group title/name.
        :param description: a description of the community
        :param purpose: what's the purpose of the community (optional)
        :param auto_approve: whether to bypass group-like request/approve process for requests
        :return: Community object

        Anyone can create a community. The creator is also the first owner.

        An owner can assign ownership to another user via share_community_with_user,
        but cannot remove self-ownership if that would leave the community with no
        owner.
        """
        if __debug__:
            assert isinstance(title, (str, unicode))
            assert isinstance(description, (str, unicode))
            if purpose:
                assert isinstance(purpose, (str, unicode))

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        raw_community = Community.objects.create(name=title, description=description,
                                                 purpose=purpose, auto_approve=auto_approve)
        raw_user = self.user

        # Must bootstrap access control system initially
        UserCommunityPrivilege.share(community=raw_community,
                                     user=raw_user,
                                     grantor=raw_user,
                                     privilege=PrivilegeCodes.OWNER)
        return raw_community

    def owns_community(self, this_community):
        """
        Boolean: is the user an owner of this community?

        :param this_community: community to check
        :return: Boolean: whether user is an owner.

        Usage:
        ------

            if my_user.owns_community(g):
                # do something that requires community ownership
                g.description='some description'
                g.save()
                my_user.unshare_community_with_group(another_user,g) # e.g.

        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return UserCommunityPrivilege.objects.filter(community=this_community,
                                                     privilege=PrivilegeCodes.OWNER,
                                                     user=self.user).exists()

    def can_change_community(self, this_community):
        """
        Return whether a user can change this community, including the effect of resource flags.

        :param this_community: community to check
        :return: Boolean: whether user can change this community.

        For communities, ownership implies change privilege but not vice versa.
        Note that change privilege does not apply to community flags, including
        active, shareable, discoverable, and public. Only owners can set these.

        Usage:
        ------

            if my_user.can_change_community(g):
                # do something that requires change privilege with g.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser:
            return True

        return this_community in self.edit_communities

    def can_view_community(self, this_community):
        """
        Whether user can view this community in entirety

        :param this_community: community to check
        :return: True if user can view this resource.

        Usage:
        ------

            if my_user.can_view_community(g):
                # do something that requires viewing g.

        See can_view_metadata below for the special case of discoverable resources.

        Note that inferred viewers -- as determined by communities -- affect view privilege,
        and these can view communities of which they are a community.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser:
            return True

        return self.user.is_superuser or \
                this_community in self.view_communities

    def can_view_community_metadata(self, this_community):
        """
        Whether user can view metadata (independent of viewing data).

        :param this_community: community to check
        :return: Boolean: whether user can view metadata

        For a community, metadata includes the community description and abstract, but not the
        member list. The member list is considered to be data.
        Being able to view metadata is a matter of being discoverable, public, or held.

        Usage:
        ------

            if my_user.can_view_metadata(some_community):
                # show metadata...
        """
        # allow access to non-logged in users for public or discoverable metadata.

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.can_view_community(this_community)

    def can_change_community_flags(self, this_community):
        """
        Whether the current user can change community flags:

        :param this_community: community to query
        :return: True if the user can set flags.

        Usage:
        ------

            if my_user.can_change_community_flags(some_community):
                some_community.active=False
                some_community.save()

        In practice:
        ------------

        This routine is called *both* when building views and when writing responders.
        It should be called on both sides of the connection.

            * In a view builder, it determines whether buttons are shown for flag changes.

            * In a responder, it determines whether the request is valid.

        At this point, the return value is synonymous with ownership or admin.
        This may not always be true. So it is best to explicitly call this function
        rather than assuming implications between functions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_community(this_community)

    def can_delete_community(self, this_community):
        """
        Whether the current user can delete a community.

        :param this_community: community to query
        :return: True if the user can delete it.

        Usage:
        ------

            if my_user.can_delete_community(some_community):
                my_user.delete_community(some_community)
            else:
                raise PermissionDenied("Insufficient privilege")

        In practice:
        --------------

        At this point, this is synonymous with ownership or admin. This may not always be true.
        So it is best to explicitly call this function rather than assuming implications
        between functions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_community(this_community)

    @property
    def communities(self):
        """
        return the communities of which a user is a member.

        A user is a member of a community if the user is a member of one group in the community.
        """
        return Community.objects.filter(c2gcp__group__g2ugp__user=self.user)

    ####################################
    # (can_)share_community_with_user: check for and implement share
    ####################################

    def can_share_community_with_user(self, this_community, this_user, this_privilege):
        """
        Return True if a given user can share this community with a specified user
        with a given privilege.

        :param self: requesting user
        :param this_community: community to check
        :param this_user: user to check
        :param this_privilege: privilege to assign to user
        :return: True if sharing is possible, otherwise false.

        This determines whether the current user can share a community with a specific user.

        Usage:
        ------

            if my_user.can_share_community_with_user(some_community, some_user,
                                                     PrivilegeCodes.VIEW):
                # ...time passes, forms are created, requests are made...
                my_user.share_community_with_user(some_community, some_user, PrivilegeCodes.VIEW)

        In practice:
        ------------

        If this returns False, UserAccess.share_community_with_user will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        if __debug__:
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        try:
            self.__check_share_community_with_user(this_community, this_user, this_privilege)
            return True
        except PermissionDenied:
            return False

    def __check_share_community_with_user(self, this_community, this_user, this_privilege):
        """

        Raise exception if a given user cannot share this community with a given privilege
        to a specific user.

        :param this_community: community to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise raise an exception.

        This determines whether the current user can share a community with a specific user.
        """
        if __debug__:
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")
        if not self.owns_community(this_community):
            raise PermissionDenied("User must own community")

    def share_community_with_user(self, this_community, this_user, this_privilege):
        """
        :param this_community: Community to be affected.
        :param this_user: User with whom to share community
        :param this_privilege: privilege to assign: 1-4
        :return: none

        User self must be one of:

                * admin
                * community owner
                * community member with shareable=True

        and have equivalent or greater privilege over community.

        Usage:
        ------

            if my_user.can_share_community(some_community, PrivilegeCodes.CHANGE):
                # ...time passes, forms are created, requests are made...
                share_community_with_user(some_community, some_user, PrivilegeCodes.CHANGE)

        In practice:
        ------------

        "can_share_community" is used to construct views with appropriate buttons or popups,
        e.g., "share with...", while "share_community_with_user" is used in the form responder
        to implement changes.  This is safe to do even if the state changes, because
        "share_community_with_user" always rechecks permissions before implementing changes.
        If -- in the interim -- one removes my_user's sharing privileges,
        "share_community_with_user" will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        # raise a PermissionDenied exception if user self is not allowed to do this.
        self.__check_share_community_with_user(this_community, this_user, this_privilege)

        UserCommunityPrivilege.share(community=this_community, user=this_user,
                                     grantor=self.user, privilege=this_privilege)

    ####################################
    # (can_)unshare_community_with_user: check for and implement unshare
    ####################################

    def unshare_community_with_user(self, this_community, this_user):
        """
        Remove a user from a community by removing privileges.

        :param this_community: Community to be affected.
        :param this_user: User with whom to unshare community
        :return: None

        This removes a user "this_user" from a community if "this_user" is not the sole owner and
        one of the following is true:
            * self is an administrator.
            * self owns the community.
            * this_user is self.

        Usage:
        ------

            if my_user.can_unshare_community_with_user(some_community, some_user):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_community_with_user(some_community, some_user)

        In practice:
        ------------

        "can_unshare_*" is used to construct views with appropriate forms and
        change buttons, while "unshare_*" is used to implement the responder to the
        view's forms. "unshare_*" still checks for permission (again) in case
        things have changed (e.g., through a stale form).
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        self.__check_unshare_community_with_user(this_community, this_user)
        UserCommunityPrivilege.unshare(community=this_community, user=this_user, grantor=self.user)

    ####################################
    # (can_)unshare_community_with_user: check for and implement unshare
    ####################################

    def can_unshare_community_with_user(self, this_community, this_user):
        """
        Determines whether a community can be unshared.

        :param this_community: community to be unshared.
        :param this_user: user to which to deny access.
        :return: Boolean: whether self can unshare this_community with this_user

        Usage:
        ------

            if my_user.can_unshare_community_with_user(some_community, some_user):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_community_with_user(some_community, some_user)

        In practice:
        ------------

        If this routine returns False, UserAccess.unshare_community_with_user is *guaranteed*
        to raise an exception.

        Note that can_unshare_X is parallel to unshare_X and returns False exactly
        when unshare_X will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)

        try:
            self.__check_unshare_community_with_user(this_community, this_user)
            return True
        except PermissionDenied:
            return False

    def __check_unshare_community_with_user(self, this_community, this_user):
        """
        Check whether an unshare of a community with a user is permitted.

        :param this_community: community with which to unshare a user.
        :param this_user: user to unshare with.

        The purpose of this utility routine is to assure that
        can_unshare_community_with_user and unshare_community_with_user
        have consistent behaviors.
        """

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)
            assert isinstance(this_user, User)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        # Check for sufficient privilege
        if not self.user.is_superuser \
                and not self.owns_community(this_community) \
                and not this_user == self.user:
            raise PermissionDenied("You do not have permission to remove this sharing setting")

        # if this_user is not an OWNER, or there is another OWNER, OK.
        if not UserCommunityPrivilege.objects.filter(community=this_community,
                                                     privilege=PrivilegeCodes.OWNER,
                                                     user=this_user).exists()\
            or UserCommunityPrivilege.objects.filter(community=this_community,
                                                     privilege=PrivilegeCodes.OWNER)\
                                             .exclude(user=this_user).exists():
            return True
        else:
            raise PermissionDenied("Cannot remove sole owner of community")

    def get_community_unshare_users(self, this_community):
        """
        Get a QuerySet of users who could be unshared from this community.

        :param this_community: community to check.
        :return: QuerySet of users who could be removed by self.

        A user can be unshared with a community if:

            * The user is self
            * Self is community owner.
            * Self has admin privilege.

        except that a user in the QuerySet cannot be the last owner of the community.

        Usage:
        ------

            c = some_community
            u = some_user
            unshare_users = request_user.get_community_unshare_users(c)
            if u in unshare_users:
                self.unshare_community_with_user(c, u)
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        access_community = this_community

        if self.user.is_superuser or self.owns_community(this_community):
            # everyone who holds this community, minus potential sole owners
            if access_community.owners.count() == 1:
                # get list of owners to exclude from main list
                # This should be one user but can be two due to race conditions.
                # Avoid races by excluding action in that case.
                users_to_exclude = User.objects.filter(is_active=True,
                                                       u2ugp__community=this_community,
                                                       u2ugp__privilege=PrivilegeCodes.OWNER)\
                                               .values('pk')
                return access_community.members.exclude(pk__in=Subquery(users_to_exclude))
            else:
                return access_community.members

        # unprivileged user can only remove grants to self, if any
        elif self.user in access_community.members:
            if access_community.owners.count() == 1:
                # if self is not an owner,
                if not UserCommunityPrivilege.objects.filter(user=self.user,
                                                             community=this_community,
                                                             privilege=PrivilegeCodes.OWNER)\
                                                     .exists():
                    # return a QuerySet containing only self
                    return User.objects.filter(uaccess=self)
                else:
                    # I can't unshare anyone
                    return User.objects.none()
            else:
                # I can unshare self as a non-owner.
                return User.objects.filter(uaccess=self)
        else:
            return User.objects.none()

    ####################################
    # (can_)share_community_with_group: check for and implement share
    ####################################

    def can_share_community_with_group(self, this_community, this_group,
                                       this_privilege=PrivilegeCodes.VIEW):
        """
        Return True if a given user can share this group with a specified group
        with a given privilege.

        :param this_group: Group to be shared.
        :param this_community: Group with which to share.
        :param this_privilege: privilege to assign to user
        :return: True if sharing is possible, otherwise false.

        This determines whether the current user can share a group with a specific second group.

        Usage:
        ------

            if my_user.can_share_community_with_group(some_community, some_group,
                        PrivilegeCodes.VIEW):
                # ...time passes, forms are created, requests are made...
                my_user.share_community_with_group(some_community, some_group, PrivilegeCodes.VIEW)

        In practice:
        ------------

        If this returns False, UserAccess.share_community_with_group will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        try:
            self.__check_share_community_with_group(this_community, this_group, this_privilege)
            return True
        except PermissionDenied:
            return False

    def __check_share_community_with_group(self, this_community, this_group,
                                           this_privilege=PrivilegeCodes.VIEW):
        """
        Check whether an unshare of a group with a community is permitted.

        :param this_community: Community with which to unshare group
        :param this_group: Group to unshare

        This utility routine's sole purpose is to ensure that
        can_share_community_with_group and share_community_with_group
        are consistent with one another.
        """
        self.__check_share_group(this_group, this_privilege)
        # only owners of the original groups can share a group with a community
        if this_privilege == PrivilegeCodes.OWNER:
            raise PermissionDenied("Groups cannot own communities")
        if not self.user.uaccess.owns_community(this_community):
            raise PermissionDenied("User must own the community to be modified")
        if not self.user.uaccess.owns_group(this_group):
            raise PermissionDenied("User must own the group that will join a community")

    def share_community_with_group(self, this_community, this_group,
                                   this_privilege=PrivilegeCodes.VIEW):
        """
        :param this_group: Group to be shared.
        :param this_community: Group with which to share.
        :param this_privilege: privilege to assign: 1-4
        :return: none

        User self must be one of:

                * admin
                * group owner
                * group member with shareable=True

        and have equivalent or greater privilege over group.

        Usage:
        ------

            if my_user.can_share_community_with_group(community, group, PrivilegeCodes.CHANGE):
                # ...time passes, forms are created, requests are made...
                my_user.share_community_with_group(community, group, PrivilegeCodes.CHANGE)

        In practice:
        ------------

        "can_share_group" is used to construct views with appropriate buttons or popups,
        e.g., "share with...", while "share_group_with_user" is used in the form responder
        to implement changes.  This is safe to do even if the state changes, because
        "share_group_with_user" always rechecks permissions before implementing changes.
        If -- in the interim -- one removes my_user's sharing privileges, "share_group_with_user"
        will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group to be shared is not active")

        # raise a PermissionDenied exception if user self is not allowed to do this.
        self.__check_share_community_with_group(this_community, this_group, this_privilege)

        GroupCommunityPrivilege.share(community=this_community, group=this_group,
                                      grantor=self.user, privilege=this_privilege)

    ####################################
    # (can_)unshare_community_with_group: check for and implement unshare
    ####################################

    def can_unshare_community_with_group(self, this_community, this_group):
        """
        Determines whether a group can be unshared.

        :param this_group: group to be unshared.
        :param this_community: group to which to deny access.
        :return: Boolean: whether self can unshare this_group with this_community

        Usage:
        ------

            if my_user.can_unshare_community_with_group(some_community, some_group):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_community_with_group(some_community, some_group)

        In practice:
        ------------

        If this routine returns False, UserAccess.unshare_community_with_group is *guaranteed*
        to raise an exception.

        Note that can_unshare_X is parallel to unshare_X and returns False exactly
        when unshare_X will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)

        try:
            self.__check_unshare_community_with_group(this_community, this_group)
            return True
        except PermissionDenied:
            return False

    def __check_unshare_community_with_group(self, this_community, this_group):
        """
        Check whether an unshare of a group with a community is permitted.

        :param this_community: Community with which to unshare group
        :param this_group: Group to unshare

        This utility routine's sole purpose is to ensure that
        can_unshare_community_with_group and unshare_community_with_group
        are consistent with one another.
        """
        if __debug__:
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group to be unshared is not active")

        if not self.user.uaccess.owns_community(this_community):
            raise PermissionDenied("User is not an owner of the target group")

        # Check for sufficient privilege
        if not self.user.is_superuser \
                and not self.owns_group(this_group):
            raise PermissionDenied("You do not have permission to remove this sharing setting")

        return True

    def unshare_community_with_group(self, this_community, this_group):
        """
        Remove a user from a group by removing privileges.

        :param this_group: Group to be unshared.
        :param this_community: Community with which to unshare.
        :return: None

        This removes a group "this_group" from a community "this_community" if
        one of the following is true:
            * self is an administrator.
            * self owns the group "this_group" and the community "this_community"

        Usage:
        ------

            if my_user.can_unshare_community_with_group(some_community, some_group):
                # ...time passes, forms are created, requests are made...
                my_user.unshare_community_with_group(some_community, some_group)

        In practice:
        ------------

        "can_unshare_*" is used to construct views with appropriate forms and
        change buttons, while "unshare_*" is used to implement the responder to the
        view's forms. "unshare_*" still checks for permission (again) in case
        things have changed (e.g., through a stale form).
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Affected Group is not active")

        self.__check_unshare_community_with_group(this_community, this_group)
        GroupCommunityPrivilege.unshare(community=this_community, group=this_group,
                                        grantor=self.user)

    def get_community_unshare_groups(self, this_community):
        """
        Get a QuerySet of groups who could be unshared from this group.

        :param this_community: group to check.
        :return: QuerySet of groups who could be removed by self.

        A group can be unshared with a group if:
            * Self is group owner.
            * Self has admin privilege.

        Usage:
        ------

            c = some_community
            g = some_group
            unshare_groups = self.get_community_unshare_groups(c)
            if g in unshare_groups:
                self.unshare_community_with_group(c, g)
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser or self.owns_community(this_community):
            return this_community.member_groups
        else:
            return Group.objects.none()

    ##################################
    # undo for communities of groups
    ##################################

    def __get_community_undo_users(self, this_community):
        """
        Get a list of users whose privilege was granted by self and can be undone.

        :param this_user: user to check.
        :returns: QuerySet of users

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, one can undo a share that one no longer has the privilege to grant.
        This excludes single owners from the list of undo users to avoid removing last owner.

        """
        if __debug__:
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        candidates = UserCommunityPrivilege.get_undo_users(community=this_community,
                                                           grantor=self.user)

        # figure out if group has a single owner
        if this_community.owners.count() == 1:
            # get list of owners to exclude from main list
            users_to_exclude = User.objects.filter(is_active=True,
                                                   u2ucp__community=this_community,
                                                   u2ucp__privilege=PrivilegeCodes.OWNER)\
                                           .values('pk')
            return candidates.exclude(pk__in=Subquery(users_to_exclude))
        else:
            return candidates

    def can_undo_share_community_with_user(self, this_community, this_user):
        """
        Check that a user share can be undone

        :param this_user: shared user to check.
        :param this_community: with user to check.
        :returns: Boolean

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus -- under freakish circumstances --  one can undo a share that one no
        longer has the privilege to grant.

        Usage:
        ------

            c = some_community
            u = some_user
            if request_user.can_undo_share_community_with_user(c,u)
                request_user.undo_share_community_with_user(c,u)
        """
        if __debug__:
            assert isinstance(this_user, User)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        return this_user in self.__get_community_undo_users(this_community)

    def undo_share_community_with_user(self, this_community, this_user):
        """
        Undo a share with a user that was granted by self

        :param this_user: user for which to remove privilege.
        :param this_community: community to remove from privilege.

        This routine undoes a privilege previously granted by self.  Only the last granted
        privilege for a user can be undone.  If some other user has granted a new (greater)
        privilege, then the new privilege cannot be undone by the original user.

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        Usage:
        ------

            c = some_community
            g = some_user
            if request_user.can_undo_share_community_with_user(c, g)
                request_user.undo_share_community_with_user(c, g)
        """

        if __debug__:
            assert isinstance(this_user, User)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_user.is_active:
            raise PermissionDenied("Grantee user is not active")

        qual_undo = self.__get_community_undo_users(this_community)
        if this_user in qual_undo:
            UserCommunityPrivilege.undo_share(user=this_user, community=this_community,
                                              grantor=self.user)
        else:
            raise PermissionDenied("User did not grant last privilege")

    def __get_community_undo_groups(self, this_community):
        """
        Get a list of groups whose privilege was granted by self and can be undone.

        :param this_group: group to check.
        :returns: QuerySet of groups

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, one can undo a share that one no longer has the privilege to grant.
        This excludes single owners from the list of undo groups to avoid removing last owner.

        """
        if __debug__:
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        return GroupCommunityPrivilege.get_undo_groups(community=this_community, grantor=self.user)

    def can_undo_share_community_with_group(self, this_community, this_group):
        """
        Check that a group share can be undone

        :param this_group: shared group to check.
        :param this_community: with group to check.
        :returns: Boolean

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus -- under freakish circumstances --  one can undo a share that one no
        longer has the privilege to grant.

        Usage:
        ------

            s = some_group
            w = some_other_group
            if request_user.can_undo_share_community_with_group(s,w)
                request_user.undo_share_community_with_group(s,w)
        """
        if __debug__:
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        return this_group in self.__get_community_undo_groups(this_community)

    def undo_share_community_with_group(self, this_community, this_group):
        """
        Undo a share with a user that was granted by self

        :param this_group: group for which to remove privilege.
        :param this_community: user to remove from privilege.

        This routine undoes a privilege previously granted by self.  Only the last granted
        privilege for a group can be undone.  If some other user has granted a new (greater)
        privilege, then the new privilege cannot be undone by the original user.

        "undo_share" differs from "unshare" in that no special privilege is required to
        "undo" a share; all that is required is that one granted the privilege initially.
        Thus, **one can undo a share that one no longer has the privilege to grant.**

        Usage:
        ------

            c = some_community
            g = some_group
            if request_user.can_undo_share_group_with_user(c, g)
                request_user.undo_share_group_with_user(c, g)
        """

        if __debug__:
            assert isinstance(this_group, Group)
            assert isinstance(this_community, Community)

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")
        if not this_group.gaccess.active:
            raise PermissionDenied("Group is not active")

        qual_undo = self.__get_community_undo_groups(this_community)
        if this_group in qual_undo:
            GroupCommunityPrivilege.undo_share(group=this_group, community=this_community,
                                               grantor=self.user)
        else:
            raise PermissionDenied("User did not grant last privilege")

    ####################################
    # get communities with specific access for a user
    ####################################

    def get_communities_with_explicit_access(self, this_privilege):
        """
        Get a QuerySet of communities for which the user has the specified privilege
        Args:
            this_privilege: one of the PrivilegeCodes

        Returns: QuerySet of Community objects (QuerySet)
        """
        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        # this query computes communities with effective privilege X as follows:
        # a) There is a privilege of X for the object for user.
        # b) There is no lower privilege for the object.
        # c) Thus X is the effective privilege of the object.
        selected = Community.objects\
            .filter(c2ucp__user=self.user,
                    c2ucp__privilege=this_privilege)\
            .exclude(pk__in=Subquery(Community.objects.filter(
                                        c2ucp__user=self.user,
                                        c2ucp__privilege__lt=this_privilege)
                                     .values("pk")))

        return selected

    def get_communities_with_explicit_membership(self, this_privilege):
        """
        Get a QuerySet of communities in which the user has explicit membership privilege
        Args:
            this_privilege: one of the PrivilegeCodes

        Returns: QuerySet of Community objects (QuerySet)
        """
        if __debug__:
            assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

        if not self.user.is_active:
            raise PermissionDenied("Requesting user is not active")

        selected = Community.objects\
            .filter(c2gcp__group__g2ugp__user=self.user,
                    c2gcp__privilege=this_privilege)\
            .exclude(pk__in=Subquery(Community.objects.filter(
                                        c2gcp__group__g2ugp__user=self.user,
                                        c2gcp__privilege__lt=this_privilege)
                                     .values("pk")))

        return selected
