__author__ = 'Pabitra'

from django.contrib.auth.models import User, Group
from django.db.models import Q

from .models import HSAUsageException, UserAccess, GroupAccess, UserGroupPrivilege, PrivilegeCodes, \
    GroupResourcePrivilege, HSAccessException, CommandCodes, ResourceAccess, UserResourcePrivilege

from hs_core.models import GenericResource


class GroupAccessHelper(object):
    @staticmethod
    def create_group(user_access, title):
            """
            Create a group.

            :param user_access: (requesting user) an object of type UserAccess representing a user who wants to create
            a group
            :param title: Group title.
            :return: Group object

            Anyone can create a group. The creator is also the first owner.

            An owner can assign ownership to another user via share_group_with_user,
            but cannot remove self-ownership if that would leave the group with no
            owner.
            """

            if not isinstance(user_access, UserAccess):
                raise HSAUsageException("user_access is not an instance of UserAccess")

            raw_group = Group(name=title) # the single attribute of the group
            raw_group.save()
            g = GroupAccess(group=raw_group)
            g.save()
            # Must bootstrap access control system initially
            UserGroupPrivilege(group=g,
                               user=user_access,
                               grantor=user_access,
                               privilege=PrivilegeCodes.OWNER).save()
            return raw_group

    @staticmethod
    def delete_group(user_access, this_group):
        """
        Delete a group and all membership information.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to delete a
        group
        :param this_group: Group to delete.
        :return: None

        To delete a group a requesting user must be owner or administrator of the group.
        Deleting a group deletes all membership and sharing information.
        There is no undo.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if user_access.admin or GroupAccessHelper.owns_group(user_access, this_group):
            # delete all references to group_id
            # default is CASCADE; this is probably unnecessary

            # remove any group privileges that might have accumulated
            UserGroupPrivilege.objects.filter(group=access_group).delete()
            GroupResourcePrivilege.objects.filter(group=access_group).delete()

            # remove access control object first: references main group
            access_group.delete()

            # get rid of the controlled object
            this_group.delete()
        else:
            raise HSAccessException("User must own group")

    @staticmethod
    def get_discoverable_groups():
        """
        Get a list of all groups marked discoverable or public.

        :return: List of discoverable groups.

        A user can view owners and abstract for a discoverable group.

        Usage:
        ------

            # fetch information about each discoverable or public group
            groups = GroupAccess.get_discoverable_groups()
            for g in groups:
                owners = g.get_owners()
                # abstract = g.abstract
                if g.public:
                    # expose group list
                    members = g.members.all()
                else:
                    members = [] # can't see them.
        """
        return Group.objects.filter(Q(gaccess__discoverable=True) | Q(gaccess__public=True))

    @staticmethod
    def get_public_groups():
        """
        Get a list of all groups marked public.

        :return: List of public groups.

        All users can list the members of a public group.  Public implies discoverable but not vice-versa.

        Usage:
        ------

            # fetch information about each public group
            groups = GroupAccess.get_public_groups()
            for g in groups:
                owners = g.get_owners()
                # abstract = g.abstract
                members = g.members.all()
                # now display member information
        """
        return Group.objects.filter(gaccess__public=True)

    @staticmethod
    def get_held_groups(user_access):
        """
        Get list of groups accessible to requesting user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants such a list
        of groups
        :return: QuerySet evaluating to held groups.

        This is really documentation of how to access held groups.

        A held group is fully accessible to the user in question, as if it were public.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return Group.objects.filter(gaccess__members=user_access)

    @staticmethod
    def get_number_of_held_groups(user_access):
        """
        Get number of groups held by requesting user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this number
        :return: Integer number of held groups.
        """
        # returning indirect objects will take too long
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return GroupAccess.objects.filter(members=user_access).count()

    @staticmethod
    def get_owned_groups(user_access):
        """
        Return a list of groups owned by self.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants such a list
        of groups
        :return: QuerySet of groups owned by requesting user.

        This requires a two-step process due to lack of understanding of the Django ORM.

        Usage:
        ------

        Because this returns a QuerySet, and not a set of objects, one can append
        extra QuerySet attributes to it, e.g. ordering, selection, projection:

            q = user.get_owned_groups()
            q2 = q.order_by(...)
            v2 = q2.values('title')
            # etc
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return Group.objects.filter(gaccess__g2ugp__user=user_access,
                                    gaccess__g2ugp__privilege=PrivilegeCodes.OWNER).distinct()

    @staticmethod
    def can_change_group(user_access, this_group):
        """
        Whether requesting user can change this group, including the effect of resource flags.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to check
        :return: Boolean: whether requesting user can change this group.

        For groups, ownership implies change privilege but not vice versa.

        Note that change privilege does not apply to group flags, including
        active, shareable, discoverable, and public. Only owners can set these.

        Usage:
        ------

            if can_change_group(requesting_user.uaccess, g):
                # do something that requires change privilege with g.


        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not user_access.active:
            return False

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege__lte=PrivilegeCodes.CHANGE,
                                             user=user_access):
            return True
        else:
            return False

    @staticmethod
    def can_view_group(user_access, this_group):
        """
        Whether user can view this group in entirety

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to check
        :return: True if requesting user can view this group.

        Usage:
        ------

            if can_view_group(requesting_user.uaccess, g):
                # do something that requires viewing g.

        See can_view_group_metadata below for the special case of discoverable groups.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        # allow access to public resources even if user is not logged in.
        if not user_access.active:
            return False
        if access_group.public:
            return True

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege__lte=PrivilegeCodes.VIEW,
                                             user=user_access):
            return True
        else:
            return False

    @staticmethod
    def can_view_group_metadata(user_access, this_group):
        """
        Whether requesting user can view metadata (independent of viewing data).

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to check
        :return: Boolean: whether requesting user can view metadata

        For a group, metadata includes the group description and abstract, but not the
        member list. The member list is considered to be data.

        Being able to view metadata is a matter of being discoverable, public, or held.

        Usage:
        ------

            if can_view_metadata(requesting_user.uaccess, some_group):
                # show metadata...

        """
        # allow access to non-logged in users for public or discoverable metadata.
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not user_access.active:
            return False

        if access_group.discoverable or access_group.public:
            return True
        else:
            return UserAccessHelper.can_view_group(user_access, this_group)

    @staticmethod
    def can_change_group_flags(user_access, this_group):
        """
        Whether the requesting user can change group flags:

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to query
        :return: True if the requesting user can set flags.

        Usage:
        ------

            if can_change_group_flags(requesting_user.uaccess, some_group):
                some_group.active=False
                some_group.save()

        In practice:
        --------------

        This routine is called *both* when building views and when writing responders.
        It should be called on both sides of the connection.

            * In a view builder, it determines whether buttons are shown for flag changes.

            * In a responder, it determines whether the request is valid.

        At this point, the return value is synonymous with ownership or admin.
        This may not always be true. So it is best to explicitly call this function
        rather than assuming implications between functions.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")

        return user_access.active and (user_access.admin or GroupAccessHelper.owns_group(user_access, this_group))

    @staticmethod
    def can_delete_group(user_access, this_group):
        """
        Whether the current user can delete a group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to query
        :return: True if the requesting user can delete this group.

        Usage:

            if can_delete_group(requesting_user.uaccess, some_group):
                delete_group(requesting_user.uaccess, some_group)
            else:
                raise HSAccessException("Insufficient privilege")

        In practice:
        --------------

        At this point, this is synonymous with ownership or admin. This may not always be true.
        So it is best to explicitly call this function rather than assuming implications
        between functions.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")

        return user_access.active and (user_access.admin or GroupAccessHelper.owns_group(user_access, this_group))

    @staticmethod
    def can_share_group(user_access, this_group, this_privilege):
        """
        If the requesting user can share this group with a given privilege.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible.

        This determines whether the requesting user can share a group, independent of
        what entity it might be shared with.

        Usage:
        ------

            if can_share_group(requesting_user.uaccess, some_group, PrivilegeCodes.VIEW):
                # ...time passes, forms are created, requests are made...
                share_group_with_user(requesting_user.uaccess, some_group, some_user, PrivilegeCodes.VIEW)

        In practice:
        ------------

        If this returns False, UserAccess.share_group_with_user will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not user_access.active:
            return False

        if not GroupAccessHelper.owns_group(user_access, this_group) and not access_group.shareable:
            return False

        # must have a this_privilege greater than or equal to what we want to assign
        if UserGroupPrivilege.objects.filter(group=access_group,
                                             user=user_access,
                                             privilege__lte=this_privilege):
            return True
        else:
            return False

    @staticmethod
    def share_group_with_user(user_access, this_group, this_user, this_privilege):
        """
        Share a group with a user

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to share a
        group with a user
        :param this_group: Group to be affected.
        :param this_user: User with whom to share group
        :param this_privilege: privilege to assign: 1-4
        :return: none

        requesting user must be one of:

                * admin

                * group owner

                * group member with shareable=True

        and have equivalent or greater privilege over group.

        Usage:
        ------

            if can_share_group(requesting_user.uaccess, some_group, PrivilegeCodes.CHANGE):
                # ...time passes, forms are created, requests are made...
                share_group_with_user(requesting_user.uaccess, some_group, some_user, PrivilegeCodes.CHANGE)

        In practice:
        ------------

        "can_share_group" is used to construct views with appropriate buttons or popups, e.g., "share with...",
        while "share_group_with_user" is used in the form responder to implement changes.

        This is safe to do even if the state changes, because "share_group_with_user" always
        rechecks permissions before implementing changes. If -- in the interim -- one removes
        _my_user_'s sharing privileges, _share_group_with_user_ will raise an exception.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        # check for user error
        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        # check for user authorization
        if not user_access.active:
            raise HSAccessException("User is not active")

        if not GroupAccessHelper.owns_group(user_access, this_group) and not access_group.shareable:
            raise HSAccessException("User is not group owner and group is not shareable")

        # must have a this_privilege greater than or equal to what we want to assign
        if not UserGroupPrivilege.objects.filter(group=access_group,
                                                 user=user_access,
                                                 privilege__lte=this_privilege):
            raise HSAccessException("User has insufficient privilege over group")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        try:
            record = UserGroupPrivilege.objects.get(group=access_group,
                                                    user=access_user,
                                                    grantor=user_access)
            if record.privilege == PrivilegeCodes.OWNER \
                    and this_privilege != PrivilegeCodes.OWNER \
                    and access_group.get_number_of_owners() == 1:
                raise HSAccessException("Cannot remove last owner of group")

            record.privilege=this_privilege
            record.save()

        except UserGroupPrivilege.DoesNotExist:
            # create a new record
            UserGroupPrivilege(group=access_group,
                               user=access_user,
                               privilege=this_privilege,
                               grantor=user_access).save()

    @staticmethod
    def __handle_unshare_group_with_user(user_access, this_group, this_user, command=CommandCodes.CHECK):
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        if not user_access.active:
            if command == CommandCodes.DO:
                raise HSAccessException("Grantor is not active")
            else:
                return False

        if access_user not in access_group.members.all():
            if command == CommandCodes.DO:
                raise HSAccessException("User is not a member of the group")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of group
        #   Modifying privileges for self
        if user_access.admin \
            or GroupAccessHelper.owns_group(user_access, this_group) \
            or access_user==user_access:
            # if there is a different owner,  we're fine
            if UserGroupPrivilege.objects.filter(group=access_group,
                                                 privilege=PrivilegeCodes.OWNER).exclude(user=access_user):
                if command == CommandCodes.DO:
                    # then remove the record.
                    # this does not return an error if the object is not shared with the user
                    UserGroupPrivilege.objects.filter(group=access_group, user=access_user).delete()
                return True  #  report success!

            else:
                # Hidden privilege other than OWNER cannot be removed for OWNERS
                if command == CommandCodes.DO:
                    raise HSAccessException("Cannot remove sole owner of group")
                else:
                    return False
        else:
            if command == CommandCodes.DO:
                raise HSAccessException("User has insufficient privilege to unshare")
            else:
                return False

    @staticmethod
    def unshare_group_with_user(user_access, this_group, this_user):
        """
        Remove a user from a group by removing privileges.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to remove a
        user from a group
        :param this_group: Group to be affected.
        :param this_user: User with whom to unshare group
        :return: Boolean

        This removes a user "this_user" from a group if "this_user" is not the sole owner and
        one of the following is true:

            * requesting user is an administrator.
            * requesting user owns the group.
            * this_user is requesting user.

        Usage:
        ------

            if can_unshare_group_with_user(requesting_user, uaccess, some_group, some_user):
                # ...time passes, forms are created, requests are made...
                unshare_group_with_user(requesting_user.uaccess, some_group, some_user)

        In practice:
        ------------

        "can_unshare_*" is used to construct views with appropriate forms and
        change buttons, while "unshare_*" is used to implement the responder to the
        view's forms. "unshare_*" still checks for permission (again) in case
        things have changed (e.g., through a stale form).
        """

        return GroupAccessHelper.__handle_unshare_group_with_user(user_access, this_group, this_user, CommandCodes.DO)

    @staticmethod
    def can_unshare_group_with_user(user_access, this_group, this_user):
        """
        Determines whether a group can be unshared.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_group: group to be unshared.
        :param this_user: user to which to deny access.
        :return: Boolean: whether requesting user can unshare this_group with this_user

        Usage:
        ------

            if can_unshare_group_with_user(requesting_user.uaccess, some_group, some_user):
                # ...time passes, forms are created, requests are made...
                unshare_group_with_user(requesting_user.uaccess, some_group, some_user)

        In practice:
        ------------

        If this routine returns False, UserAccess.unshare_group_with_user is *guaranteed*
        to raise an exception.
        """
        return GroupAccessHelper.__handle_unshare_group_with_user(user_access, this_group, this_user,
                                                                  CommandCodes.CHECK)

    @staticmethod
    def __handle_undo_share_group_with_user(user_access, this_group, this_user, command=CommandCodes.CHECK,
                                            this_grantor=None):
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None:
            if not isinstance(this_grantor, User):
                raise HSAUsageException("Grantor is not a user")
            access_grantor = this_grantor.uaccess
            if not UserGroupPrivilege.objects.filter(group=access_group,
                                                     user=access_user,
                                                     grantor=access_grantor):
                if command == CommandCodes.DO:
                    raise HSAccessException("Grantor did not grant privilege")
                else:
                    return False

            if not GroupAccessHelper.owns_group(user_access, this_group) and not user_access.admin:
                if command == CommandCodes.DO:
                    raise HSAccessException("Self must be owner or admin")
                else:
                    return False
        else:
            access_grantor = user_access

        if not user_access.active:
            if command == CommandCodes.DO:
                raise HSAccessException("Grantor is not active")
            else:
                return False

        if access_user not in access_group.members.all():
            if command == CommandCodes.DO:
                raise HSAccessException("User is not a member of the group")
            else:
                return False
        try:
            existing = UserGroupPrivilege.objects.get(group=access_group,
                                                      user=access_user,
                                                      grantor=user_access)
            # if the privilege for user is not OWNER,
            # or there's another OWNER:
            if existing.privilege != PrivilegeCodes.OWNER \
                    or UserGroupPrivilege.objects \
                          .filter(group=access_group,
                                  privilege=PrivilegeCodes.OWNER) \
                          .exclude(user=access_user, grantor=access_grantor):
                if command == CommandCodes.DO:
                    # then remove the record.
                    # this does not return an error if the object is not shared with the user
                    UserGroupPrivilege.objects.filter(group=access_group,
                                                      user=access_user,
                                                      grantor=access_grantor).delete()
                return True
            else:
                if command == CommandCodes.DO:
                    raise HSAccessException("Cannot remove sole owner of group")
                else:
                    return False
        except UserGroupPrivilege.DoesNotExist:
            if command == CommandCodes.DO:
                raise HSAccessException("No share to undo")
            else:
                return False

    @staticmethod
    def undo_share_group_with_user(user_access, this_group, this_user, this_grantor=None):
        """
        Remove a user from a group who was assigned by self.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare
        a group with a user
        :param this_group: group to affect.
        :param this_user: user with whom to unshare group.
        :return: None

        This removes one share for a user in the case where that share was
        assigned by requesting user, and the removal does not leave the group without
        an owner.

        Usage:
        ------

            if can_undo_share_group_with_user(requesting_user.uaccess, some_group, some_user):
                # ...time passes, forms are created, requests are made...
                undo_share_group_with_user(requesting_user.uaccess, some_group, some_user)

        In practice:
        ------------

        "can_undo_share_*" is used to construct views with appropriate forms and
        change buttons, while "undo_share_*" is used to implement the responder to the
        view's forms. "undo_share_*" still checks for permission (again) in case
        things have changes (e.g., through a stale form).
        """
        return GroupAccessHelper.__handle_undo_share_group_with_user(user_access, this_group, this_user,
                                                                     CommandCodes.DO, this_grantor)

    @staticmethod
    def can_undo_share_group_with_user(user_access, this_group, this_user, this_grantor=None):
        """
        Check whether we can remove a user from a group who was assigned by self.

        :param user_access: an object of type UserAccess
        :param this_group: group to affect.
        :param this_user: user with whom to unshare group.
        :return: None

        This removes one share for a user in the case where that share was
        assigned by self, and the removal does not leave the group without
        an owner.

        Usage:
        ------

            if my_user.can_undo_share_group_with_user(some_group, some_user):
                # ...time passes, forms are created, requests are made...
                my_user.undo_share_group_with_user(some_group, some_user)

        In practice:
        ------------
        This returns True exactly when "undo_share_group_with_user" does not
        raise an exception.

        Thus, this can be used to condition views by only providing options that
        will work.

            * In a group view, use "can_undo" to create "undo share" buttons only when
              user has privilege.
            * In the responder, use the corresponding "undo_share" to accomplish the undo.

        Note that this is safe to do even if the state changes, because "undo_share"
        in the responder will always recheck that its actions are permissible before
        doing them.

        """

        return GroupAccessHelper.__handle_undo_share_group_with_user(user_access, this_group, this_user,
                                                                     CommandCodes.CHECK, this_grantor)

    @staticmethod
    def get_group_undo_users(user_access, this_group):
        """
        Get a list of users to whom self granted access

        :param user_access: an object of type UserAccess
        :param this_group: group to check.
        :return: list of users granted access by self.

        These are the users for which an unprivileged user can call
        undo_share_group_with_users

        Usage:
        ------
            # g is a target group
            # u is a target user
            undo_users = self.get_group_undo_users(g)
            if u in undo_users:
                self.undo_share_group_with_user(g, u)
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if user_access.admin or GroupAccessHelper.owns_group(user_access, this_group):

            if access_group.get_number_of_owners()>1:
                # every possible undo is permitted, including self-undo
                return User.objects.filter(uaccess__held_groups=access_group)
            else:  # exclude sole owner from undo
                return User.objects.filter(uaccess__u2ugp__group=access_group)\
                                   .exclude(uaccess__u2ugp__group=access_group,
                                            uaccess__u2ugp__privilege=PrivilegeCodes.OWNER)
        else:
            if access_group.get_number_of_owners()>1:
                return User.objects.filter(uaccess__u2ugp__grantor=user_access, uaccess__u2ugp__group=access_group)

            else:  # exclude sole owner from undo

                # The following is a tricky query
                # a) I need to match for one record in u2ugp, which means that
                #    the matches have to be in the same filter()
                # b) I need to exclude matches with one extra attribute.
                #    Thus I must repeat attributes in the exclude.
                return User.objects.filter(uaccess__u2ugp__group=access_group,
                                           uaccess__u2ugp__grantor=user_access)\
                                   .exclude(uaccess__u2ugp__group=access_group,
                                            uaccess__u2ugp__grantor=user_access,
                                            uaccess__u2ugp__privilege=PrivilegeCodes.OWNER)

    @staticmethod
    def get_group_unshare_users(user_access, this_group):
        """
        Get a list of users who could be unshared from this group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to get this
        list of users
        :param this_group: group to check.
        :return: list of users who could be removed by requesting user.

        A user can be unshared with a group if:

            * The user is requesting user
            * requesting user is group owner.
            * requesting user has admin privilege.

        except that a user in the list cannot be the last owner of the group.

        Usage:
        ------

            g = some_group
            u = some_user
            unshare_users = get_group_unshare_users(requesting_user.uaccess, g)
            if u in unshare_users:
                unshare_group_with_user(requesting_user.uaccess, g, u)
        """
        # Users who can be removed fall into three categories
        # a) requesting user is admin: everyone.
        # b) requesting user is group owner: everyone.
        # c) requesting user is beneficiary: self only
        # Except that a user in the list cannot be the last owner.
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if user_access.admin or GroupAccessHelper.owns_group(user_access, this_group):
            # everyone who holds this resource, minus potential sole owners
            if access_group.get_number_of_owners() == 1:
                # get list of owners to exclude from main list
                ids_exclude = UserGroupPrivilege.objects\
                        .filter(group=access_group, privilege=PrivilegeCodes.OWNER)\
                        .values_list('user_id', flat=True)\
                        .distinct()
                return access_group.get_members().exclude(uaccess__pk__in=ids_exclude)
            else:
                return access_group.get_members()
        elif user_access in access_group.holding_users.all():
            if access_group.get_number_of_owners == 1:
                # if I'm not that owner
                if not UserGroupPrivilege.objects\
                        .filter(user=user_access, group=access_group, privilege=PrivilegeCodes.OWNER):
                    # this is a fancy way to return self as a QuerySet
                    # I can remove myself
                    return User.objects.filter(uaccess=user_access)
                else:
                    # I can't remove anyone
                    return User.objects.filter(uaccess=None)  # empty set
        else:
            return User.objects.filter(uaccess=None)  # empty set

    @staticmethod
    def owns_group(user_access, this_group):
        """
        Boolean: is the user an owner of this group?

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to check if
        he/she owns the group
        :param this_group: group to check
        :return: Boolean: whether requesting user is an owner.

        Usage:
        ------

            if owns_group(requesting_user.uaccess, g):
                # do something that requires group ownership
                g.public=True
                g.discoverable=True
                g.save()
                unshare_user_with_group(requesting_user.uaccess, g, another_user) # e.g.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege=PrivilegeCodes.OWNER,
                                             user=user_access):
            return True
        else:
            return False

    @staticmethod
    def share_resource_with_group(user_access, this_resource, this_group, this_privilege):
        """
        Share a resource with a group

        :param user_access: (requesting user) an object of type UserAccess representing a user wanting to share
        a resource with a group
        :param this_resource: Resource to share.
        :param this_group: User with whom to share resource
        :param this_privilege: privilege to assign: 1-4
        :return: None

        Assigning user (requesting user) must be admin, owner, or have equivalent privilege over resource.
        Assigning user (requesting user) must be a member of the group.
        """

        # check for user error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if this_privilege == PrivilegeCodes.OWNER:
            raise HSAccessException("Groups cannot own resources")
        if this_privilege < PrivilegeCodes.OWNER or this_privilege > PrivilegeCodes.VIEW:
            raise HSAccessException("Privilege level not valid")

        # check for user authorization
        if not UserAccessHelper.can_share_resource(user_access, this_resource, this_privilege):
            raise HSAccessException("User has insufficient sharing privilege over resource")

        if user_access not in access_group.members.all():
            raise HSAccessException("User is not a member of the group")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        try:
            record = GroupResourcePrivilege.objects.get(resource=access_resource,
                                                        group=access_group,
                                                        grantor=user_access)

            # record.start=timezone.now() # now automatically set
            record.privilege=this_privilege
            record.save()

        except GroupResourcePrivilege.DoesNotExist:
            # create a new record
            GroupResourcePrivilege(resource=access_resource,
                                   group=access_group,
                                   privilege=this_privilege,
                                   grantor=user_access).save()

    @staticmethod
    def __handle_unshare_resource_with_group(user_access, this_resource, this_group, command=CommandCodes.CHECK):
        # first check for usage error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        if access_group not in access_resource.holding_groups.all():
            if command == CommandCodes.DO:
                raise HSAccessException("Group does not have access to resource")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of resource
        #   Owner of group
        if user_access.admin \
                or UserAccessHelper.owns_resource(user_access, this_resource) \
                or GroupAccessHelper.owns_group(user_access, this_group):

            # this does not return an error if the object is not shared with the user
            if command == CommandCodes.DO:
                GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                      group=access_group).delete()
            return True

        else:
            if command == CommandCodes.DO:
                raise HSAccessException("Insufficient privilege to unshare resource")
            else:
                return False

    @staticmethod
    def unshare_resource_with_group(user_access, this_resource, this_group):
        """
        Remove a group from access to a resource by removing privileges.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare a
        resource with a group
        :param this_resource: resource to be affected.
        :param this_group: group with which to unshare resource
        :return: None

        This removes a group "this_group" from access to "this_resource" if one of the following is true:

            * requesting user is an administrator.
            * requesting user owns the resource.
            * requesting user owns the group.

        """
        return GroupAccessHelper.__handle_unshare_resource_with_group(user_access, this_resource, this_group,
                                                                      CommandCodes.DO)

    @staticmethod
    def can_unshare_resource_with_group(user_access, this_resource, this_group):
        """
        Check whether one can unshare a resource with a group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to check he/she
        can unshare a resource with a group
        :param this_resource: resource to be protected.
        :param this_group: group with which to unshare resource.
        :return: None

        Unsharing will remove a group "this_group" from access to "this_resource" if one of the following is true:

            * requesting user is an administrator.
            * requesting user owns the resource.
            * requesting user owns the group.

        This routine returns False exactly when unshare_resource_with_group will raise an exception.
        """
        return GroupAccessHelper.__handle_unshare_resource_with_group(user_access, this_resource, this_group,
                                                                      CommandCodes.CHECK)

    @staticmethod
    def get_resource_undo_groups(user_access, this_resource):
        """
        Get a list of groups to whom requesting user granted access

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this list of
        groups
        :param this_resource: resource to check.
        :return: list of groups granted access by requesting user.

        A user (requesting user) can undo a privilege if

            1. That privilege was assigned by this user.
            2. User owns the resource
            3. User owns the group -- *not implemented*
            4. User is an administrator
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource):
            return Group.objects.filter(gaccess__held_resources=access_resource).distinct()
        else:  #  privilege only for grantor
            return Group.objects.filter(gaccess__g2grp__resource=access_resource,
                                        gaccess__g2grp__grantor=user_access).distinct()

    @staticmethod
    def get_resource_unshare_groups(user_access, this_resource):
        """
        Get a list of groups who could be unshared from this resource.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this list of
        groups
        :param this_resource: resource to check.
        :return: list of groups who could be removed by requesting user.

        This is a list of groups for which unshare_resource_with_group will work for this user.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        # Users who can be removed fall into three catagories
        # a) requesting user is admin: everyone with access.
        # b) requesting user is resource owner: everyone with access.
        # c) requesting user is group owner: only for owned groups

        # if requesting user is administrator or owner, then return all groups with access.

        if user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource):
            # all shared groups
            return Group.objects.filter(gaccess__held_resources=access_resource)
        else:
            return Group.objects.filter(gaccess__g2ugp__user=user_access,
                                        gaccess__g2ugp__privilege=PrivilegeCodes.OWNER).distinct()


class UserAccessHelper(object):

    @staticmethod
    def get_held_resources(user_access):
        """
        Get a list of resources held by requesting user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this list of
        resources
        :return: List of resource objects accessible (in any form) to requesting user.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return GenericResource.objects.filter(Q(raccess__holding_users=user_access) |
                                              Q(raccess__holding_groups__members=user_access))

    @staticmethod
    def get_number_of_held_resources(user_access):
        """
        Get the number of resources held by user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this number
        :return: Integer number of resources accessible for requesting user.
        """
        # utilize simpler join-free query that that of get_held_resources()
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return ResourceAccess.objects.filter(Q(holding_users=user_access) |
                                             Q(holding_groups__members=user_access)).count()

    @staticmethod
    def get_owned_resources(user_access):
        """
        Get a list of resources owned by requesting user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this list of
        resources
        :return: List of resources owned by requesting user.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return GenericResource.objects.filter(raccess__r2urp__user=user_access,
                                              raccess__r2urp__privilege=PrivilegeCodes.OWNER).distinct()

    @staticmethod
    def get_number_of_owned_resources(user_access):
        """
        Get number of resources owned by self.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this number
        :return: Integer number of resources owned by requesting user.

        This is a separate procedure, rather than get_owned_resources().count(), due to performance concerns.
        """
        # This is a join-free query; get_owned_resources includes a join.
        return UserAccessHelper.get_owned_resources(user_access).count()

    @staticmethod
    def get_editable_resources(user_access):
        """
        Get a list of resources that can be edited by user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants this list of
        resources
        :return: List of resources that can be edited  by requesting user.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        return GenericResource.objects.filter(raccess__r2urp__user=user_access, raccess__immutable=False,
                                              raccess__r2urp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    @staticmethod
    def owns_resource(user_access, this_resource):
        """
        Boolean: is the requesting user an owner of this resource?

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :return: Boolean: whether requesting user is an owner or not

        Note that the fact that someone owns a resource is not sufficient proof that
        one has permission to change it, because resource flags can override the raw
        privilege. It is thus necessary to check that one can change something
        explicitly, using UserAccess.can_change_resource()
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege=PrivilegeCodes.OWNER,
                                                user=user_access):
            return True
        else:
            return False

    @staticmethod
    def can_change_resource(user_access, this_resource):
        """
        Return whether requesting user can change this resource, including the effect of resource flags.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :return: Boolean: whether requesting user can change this resource.

        This result is advisory and is not enforced. The Django application must enforce this
        policy, using this routine for guidance.

        Note that the ability to change a resource is not just contingent upon sharing,
        but also upon the resource flag "immutable". Thus "owns" does not imply "can change" privilege.

        Note also that the ability to change a resource applies to its data and metadata, but not to its
        resource state flags: shareable, public, immutable, published, and discoverable.

        We elected not to return a queryset for this one, because that would mean that it
        would return two types depending upon conditions -- Boolean for simple queries and
        QuerySet for complex queries.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not user_access.active:
            return False

        if access_resource.immutable:
            return False

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege__lte=PrivilegeCodes.CHANGE,
                                                user=user_access):
            return True

        if GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                 privilege__lte=PrivilegeCodes.CHANGE,
                                                 group__members=user_access):
            return True

        return False

    @staticmethod
    def can_change_resource_flags(user_access, this_resource):
        """
        Whether self can change resource flags.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: Resource to check.
        :return: True if requesting user can set flags, otherwise false

        This is not enforced. It is up to the programmer to obey this restriction.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")

        return user_access.active and (user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource))

    @staticmethod
    def can_view_resource(user_access, this_resource):
        """
        Whether user can view this resource

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: Resource to check
        :return: True if requesting user can view this resource, otherwise false

        Note that one can view resources that are public, that one does not own.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not user_access.active:
            return False

        if access_resource.public:
            return True

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege__lte=PrivilegeCodes.VIEW,
                                                user=user_access):
            return True

        if GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                 privilege__lte=PrivilegeCodes.VIEW,
                                                 group__members=user_access):
            return True

        return False

    @staticmethod
    def can_delete_resource(user_access, this_resource):
        """
        Whether user can delete a resource

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: Resource to check.
        :return: True if requesting user can delete the resource, otherwise false
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")

        return user_access.active and (user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource))

    @staticmethod
    def can_share_resource(user_access, this_resource, this_privilege):
        """
        Can a resource be shared by the requesting user?

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: resource to check
        :param this_privilege: privilege to assign
        :return: Boolean: whether resource can be shared by the requesting user, otherwise false

        In this computation, user target of sharing is not relevant.
        One can share with self, which can only downgrade privilege.
        """
        # translate into ResourceAccess object
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not user_access.active:
            return False

        # access control logic: Can change privilege if
        #   Admin
        #   Owner
        #   Privilege for self
        whom_priv = access_resource.get_combined_privilege(user_access.user)

        # check for user authorization
        if user_access.admin:
            pass  # admin can do anything

        elif whom_priv == PrivilegeCodes.OWNER:
            pass  # owner can do anything

        elif access_resource.shareable:
            pass  # non-owners can share

        else:
            return False

        # no privilege over resource
        if whom_priv > PrivilegeCodes.VIEW:
            return False

        # insufficient privilege over resource
        if whom_priv > this_privilege:
            return False

        return True

    @staticmethod
    def can_share_resource_with_group(user_access, this_resource, this_group, this_privilege):
        """
        Check whether requesting user can share a resource with a group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: resource to share.
        :param this_group: group with which to share it.
        :param this_privilege: privilege level of sharing.
        :return: Boolean: whether requesting user can share

        This function returns False exactly when share_resource_with_group will raise
        an exception if called.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")

        if this_privilege==PrivilegeCodes.OWNER:
            return False

        # check for user authorization
        # a) user must have privilege over resource
        # b) user must be in the group
        if not UserAccessHelper.can_share_resource(user_access, this_resource, this_privilege):
            return False

        if user_access not in this_group.members:
            return False

        return True

    @staticmethod
    def __handle_undo_share_resource_with_group(user_access, this_resource, this_group, command=CommandCodes.CHECK,
                                                this_grantor=None):
        # first check for usage error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None and this_grantor.uaccess != user_access:
            if not isinstance(this_grantor, User):
                raise HSAUsageException("Grantor is not a user")

            access_grantor = this_grantor.uaccess

            if not UserAccessHelper.owns_resource(user_access, this_resource) and not user_access.admin:
                if command == CommandCodes.DO:
                    raise HSAccessException("Self must be owner or admin")
                else:
                    return False  # non-owners cannot specify grantor

            if not GroupResourcePrivilege.objects.filter(group=access_group,
                                                         resource=access_resource,
                                                         grantor=access_grantor):
                # print('non-default: no grant for '+access_grantor.user.first_name)
                if command == CommandCodes.DO:
                    raise HSAccessException("No privilege to remove")
                else:
                    return False
        else:
            access_grantor = user_access

        if GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                 group=access_group,
                                                 grantor=access_grantor):
            if command == CommandCodes.DO:
                GroupResourcePrivilege.objects.get(resource=access_resource,
                                                   group=access_group,
                                                   grantor=access_grantor).delete()
            return True  # return success
        else:
            if command == CommandCodes.DO:
                raise HSAccessException("Grantor did not grant privilege")
            else:
                return False

    @staticmethod
    def undo_share_resource_with_group(user_access, this_resource, this_group, this_grantor=None):
        """
        Remove resource privileges self-granted to a group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare
        a resource with a group that he/she originally granted access
        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: True if resource unsharing with group is successful, otherwise false

        This tries to remove one user access record for "this_group" and "this_resource"
        if grantor is requesting user. If this_grantor is specified, that is utilized as grantor as long as
        requesting user is owner or admin.
        """
        return UserAccessHelper.__handle_undo_share_resource_with_group(user_access, this_resource,
                                                                        this_group,
                                                                        CommandCodes.DO,
                                                                        this_grantor)

    @staticmethod
    def can_undo_share_resource_with_group(user_access, this_resource, this_group, this_grantor=None):
        """
        Check whether the requesting user can remove resource privileges self-granted to a group.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: True if requesting user can unshare resource with group, otherwise false

        This checks whether one can remove one user access record for "this_group" and "this_resource"
        if grantor is self. If this_grantor is specified, that is utilized as the grantor as long as
        self is owner or admin.
        """
        return UserAccessHelper.__handle_undo_share_resource_with_group(user_access, this_resource,
                                                                        this_group,
                                                                        CommandCodes.CHECK,
                                                                        this_grantor)

    @staticmethod
    def share_resource_with_user(user_access, this_resource, this_user, this_privilege):
        """
        Share a resource with a specific (third-party) user

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to share
        resource with a user
        :param this_resource: Resource to be shared.
        :param this_user: User with whom to share resource
        :param this_privilege: privilege to assign: 1-4
        :return: none

        Assigning user (requesting user) must be admin, owner, or have equivalent privilege over resource.
        """

        # check for user error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        # this is parallel to can_share_resource_with_user(this_resource, this_privilege)

        if not user_access.active:
            raise HSAccessException("Requester is not an active user")

        # access control logic: Can change privilege if
        #   Admin
        #   Self-set permission
        #   Owner
        #   Non-owner and shareable
        whom_priv = access_resource.get_combined_privilege(user_access.user)

        # check for user authorization

        if user_access.admin:
            pass  # admin can do anything

        elif whom_priv == PrivilegeCodes.OWNER:
            pass  # owner can do anything

        elif access_resource.shareable:
            pass  # non-owners can share

        else:
            raise HSAccessException("User must own resource or have sharing privilege")

        # privilege checking

        if whom_priv > PrivilegeCodes.VIEW:
            raise HSAccessException("User has no privilege over resource")

        if whom_priv > this_privilege:
            raise HSAccessException("User has insufficient privilege over resource")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        try:
            record = UserResourcePrivilege.objects.get(resource=access_resource,
                                                       user=access_user,
                                                       grantor=user_access)
            if record.privilege==PrivilegeCodes.OWNER \
                    and this_privilege!=PrivilegeCodes.OWNER \
                    and access_resource.get_number_of_owners() == 1:
                raise HSAccessException("Cannot remove last owner of resource")

            # record.start=timezone.now() # now automatically set
            record.privilege = this_privilege
            record.save()

        except UserResourcePrivilege.DoesNotExist:
            # create a new record
            UserResourcePrivilege(resource=access_resource,
                                  user=access_user,
                                  privilege=this_privilege,
                                  grantor=user_access).save()

    @staticmethod
    def __handle_unshare_resource_with_user(user_access, this_resource, this_user, command=CommandCodes.CHECK):

        """
        Remove a user from a resource by removing privileges.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare a
        resource with a user
        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :param command: command code to perform
        :return: Boolean

        This removes a user "this_user" from resource access to "this_resource" if one of the following is true:

            * requesting user is an administrator.

            * requesting user owns the group.

            * requesting user is the grantee of resource access.

        *and* removing the user will not lead to a resource without an owner.

        There is no provision for revoking lower-level permissions for an owner.
        If a user is a sole owner and holds other privileges, this call will not remove them.
        """

        # first check for usage error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        if access_user not in access_resource.holding_users.all():
            if command == CommandCodes.DO:
                raise HSAccessException("User does not have access to resource")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of resource
        #   Modifying self
        if user_access.admin \
                or access_resource.get_combined_privilege(user_access.user) == PrivilegeCodes.OWNER \
                or access_user == user_access:
            if UserResourcePrivilege.objects \
                    .filter(resource=access_resource,
                            privilege=PrivilegeCodes.OWNER) \
                    .exclude(user=access_user):
                # then remove the record.
                # this does not return an error if the object is not shared with the user
                if command == CommandCodes.DO:
                    UserResourcePrivilege.objects.filter(resource=access_resource,
                                                         user=access_user).delete()
                return True  # indicate success
            else:
                # this prevents one from removing privilege for a user
                # if any grant is owner. This protects the other grants as well.
                if command == CommandCodes.DO:
                    raise HSAccessException("Cannot remove sole resource owner")
                else:
                    return False
        else:
            if command == CommandCodes.DO:
                raise HSAccessException("Insufficient privilege to unshare resource")
            else:
                return False

    @staticmethod
    def unshare_resource_with_user(user_access, this_resource, this_user):
        """
        Unshare a resource with a specific user, removing all privilege for that user

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare
        resource with a user
        :param this_resource: Resource to unshare
        :param this_user:  User with whom to unshare resource.
        :return: True if it is unshared successfully.
        """
        return UserAccessHelper.__handle_unshare_resource_with_user(user_access, this_resource, this_user,
                                                                    CommandCodes.DO)

    @staticmethod
    def can_unshare_resource_with_user(user_access, this_resource, this_user):
        """
        Check whether one can dissociate a specific user from a resource

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether requesting user can unshare resource with a user.

        This checks if both of the following are true:

            * requesting user is administrator, or owns the resource.

            * This act does not remove the last owner of the resource.

        If so, it removes all privilege over this_resource for this_user.

        To remove a single privilege, rather than all privilege,
        see can_undo_share_resource_with_user
        """
        return UserAccessHelper.__handle_unshare_resource_with_user(user_access, this_resource, this_user,
                                                                    CommandCodes.CHECK)

    @staticmethod
    def __handle_undo_share_resource_with_user(user_access, this_resource, this_user, command=CommandCodes.CHECK,
                                               this_grantor=None):
        """
        Remove a self-granted privilege from a user.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to unshare a
        resource with a user
        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :return: None

        This removes a user "this_user" from resource access to "this_resource" if requesting user granted the
        privilege, *and* removing the user will not lead to a resource without an owner.
        """

        # first check for usage error
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None:
            if not isinstance(this_grantor, User):
                raise HSAUsageException("Grantor is not a user")
            access_grantor = this_grantor.uaccess

            if not GroupResourcePrivilege.objects.filter(user=access_user,
                                                         resource=access_resource,
                                                         grantor=access_grantor):
                if command == CommandCodes.DO:
                    raise HSAccessException("Grantor did not grant privilege")
                else:
                    return False

            if not UserAccessHelper.owns_resource(user_access, this_resource) and not user_access.admin:
                if command == CommandCodes.DO:
                    raise HSAccessException("Self must be owner or admin")
                else:
                    return False
        else:
            access_grantor = user_access

        try:
            existing = UserResourcePrivilege.objects.get(resource=access_resource,
                                                     user=access_user,
                                                     grantor=access_grantor)
            # if there is an owner other than the grantee, or the grantee is not an owner
            if existing.privilege != PrivilegeCodes.OWNER \
                    or UserResourcePrivilege.objects.filter(resource=access_resource,
                                                            privilege=PrivilegeCodes.OWNER) \
                                                    .exclude(resource=access_resource,
                                                             user=access_user,
                                                             grantor=access_grantor):
                # then remove the record.
                # this does not return an error if the object is not shared with the user
                if command == CommandCodes.DO:
                    UserResourcePrivilege.objects.filter(resource=access_resource,
                                                         user=access_user,
                                                         grantor=access_grantor).delete()
                return True  # Indicate success!

            else:
                # this prevents one from removing privilege for a user
                # if any grant is owner. This protects the other grants as well.
                if command == CommandCodes.DO:
                    raise HSAccessException("Cannot remove sole resource owner")
                else:
                    return False

        except UserResourcePrivilege.DoesNotExist:
            if command == CommandCodes.DO:
                raise HSAccessException("No share to undo")
            else:
                return False

    @staticmethod
    def undo_share_resource_with_user(user_access, this_resource, this_user, this_grantor=None):
        return UserAccessHelper.__handle_undo_share_resource_with_user(user_access, this_resource, this_user,
                                                                       CommandCodes.DO, this_grantor)

    @staticmethod
    def can_undo_share_resource_with_user(user_access, this_resource, this_user, this_grantor=None):
        """
        Check whether one can dissociate a specific user from a resource

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to do this
        check
        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether requesting user can unshare this resource with this user.

        This checks if both of the following are true:

            * requesting user is administrator, or owns the resource.

            * This act does not remove the last owner of the resource.

        If so, it removes all privilege over this_resource for this_user.

        To remove a single privilege, rather than all privilege,
        see can_undo_share_resource_with_user
        """
        return UserAccessHelper.__handle_undo_share_resource_with_user(user_access, this_resource, this_user,
                                                                       CommandCodes.CHECK, this_grantor)

    @staticmethod
    def get_resource_undo_users(user_access, this_resource):
        """
        Get a list of users to whom requesting user granted access

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants to get this
        list of users
        :param this_resource: resource to check.
        :return: list of users granted access by requesting user.
        """
        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource):

            if access_resource.get_number_of_owners()>1:
                # print("Returning results for all undoes -- owners>1")
                return User.objects.filter(uaccess__held_resources=access_resource)
            else:  # exclude sole owner from undo
                # print("Returning results for non-owner undos -- owners==1")
                # We need to return the users who are not owners, not the users who have privileges other than owner
                # all candidate undos
                ids_shared = UserResourcePrivilege.objects.filter(resource=access_resource)\
                                                   .values_list('user_id', flat=True).distinct()
                # undoes that will remove sole owner
                ids_owner = UserResourcePrivilege.objects.filter(resource=access_resource,
                                                                 privilege=PrivilegeCodes.OWNER)\
                                                   .values_list('user_id', flat=True).distinct()
                # return difference
                return User.objects.filter(uaccess__held_resources=access_resource, uaccess__pk__in=ids_shared)\
                                   .exclude(uaccess__pk__in=ids_owner)
        else:
            if access_resource.get_number_of_owners()>1:
                # self is grantor
                return User.objects.filter(uaccess__u2urp__grantor=user_access,
                                           uaccess__u2urp__resource=access_resource).distinct()

            else:  # exclude sole owner from undo
                return User.objects.filter(uaccess__u2urp__grantor=user_access,
                                           uaccess__u2urp__resource=access_resource)\
                                   .exclude(uaccess__u2urp__grantor=user_access,
                                            uaccess__u2urp__resource=access_resource,
                                            uaccess__u2urp__privilege=PrivilegeCodes.OWNER).distinct()

    @staticmethod
    def get_resource_unshare_users(user_access, this_resource):
        """
        Get a list of users who could be unshared from this resource.

        :param user_access: (requesting user) an object of type UserAccess representing a user who wants such a list of
        users
        :param this_resource: resource to check.
        :return: list of users who could be removed by requesting user.
        """
        # Users who can be removed fall into three catagories
        # a) requesting user is admin: everyone.
        # b) requesting user is resource owner: everyone.
        # c) requesting user is beneficiary: self only

        if not isinstance(user_access, UserAccess):
            raise HSAUsageException("user_access is not an instance of UserAccess")

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if user_access.admin or UserAccessHelper.owns_resource(user_access, this_resource):
            # everyone who holds this resource, minus potential sole owners
            if access_resource.get_number_of_owners() == 1:
                # get list of owners to exclude from main list
                ids_exclude = UserResourcePrivilege.objects\
                        .filter(resource=access_resource, privilege=PrivilegeCodes.OWNER)\
                        .values_list('user_id', flat=True)\
                        .distinct()
                return access_resource.get_users().exclude(uaccess__pk__in=ids_exclude)
            else:
                return access_resource.get_users()
        elif user_access in access_resource.holding_users.all():
            return User.objects.filter(uaccess=user_access)
        else:
            return User.objects.filter(uaccess=None)  # empty set


class AccessControlHelper(UserAccessHelper, GroupAccessHelper):
    pass