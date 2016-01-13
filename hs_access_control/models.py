"""
Access control classes for hydroshare. 

This module implements access control for hydroshare. 

"""
__author__ = 'Alva'

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.db import transaction
from django.conf import settings
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource

######################################
# Access control subsystem
######################################

# TODO: basic polymorphic routines user.can_change, user.can_view
# TODO: ensure that user is_active flags work properly in access control queries.
# TODO: there is a small chance of a race condition that could result in removal of the last resource or group owner. Use transaction blocks. 
# TODO: eradicate group active flag from all routines. 

####################################
# Privilege models determine what objects are accessible to which users
# These models:
# a) determine three kinds of privilege
#    i) user membership in and privilege over groups.
#    ii) user privilege over resources.
#    ii) group privilege over resources.
# b) track the provenance of privilege granting to:
#    i) allow accounting for what happened.
#    ii) allow "undo" operations.
#    iii) limit each grantor to granting one privilege
####################################

class PrivilegeCodes(object):
    """
    Privilege codes describe what capabilities a user has for a thing
    Privilege is a numeric code 1-4:

        * 1 or PrivilegeCodes.OWNER:
            the user owns the object.

        * 2 or PrivilegeCodes.CHANGE:
            the user can change the content of the object but not its state.

        * 3 or PrivilegeCodes.VIEW:
            the user can view but not change the object.

        * 4 or PrivilegeCodes.NONE:
            the user has no privilege over the object.
    """
    OWNER = 1
    CHANGE = 2
    VIEW = 3
    NONE = 4
    PRIVILEGE_CHOICES = (
        (OWNER, 'Owner'),
        (CHANGE, 'Change'),
        (VIEW, 'View')
        # (NONE, 'None') : disallow "no privilege" lines
    )


class CommandCodes(object):
    """
    Command codes describe nature of a request.
    """
    CHECK = 1
    DO = 2


class UserGroupPrivilege(models.Model):
    """ Privileges of a user over a group

    Having any privilege over a group is synonymous with membership.

    There is a reasonable meaning to PrivilegeCodes.NONE, which is to be
    a group member without the ability to discover the identities of other 
    group members.  However, this is currently disallowed.
    """

    privilege = models.IntegerField(choices=PrivilegeCodes.PRIVILEGE_CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    start = models.DateTimeField(editable=False, auto_now=True)

    # in the prior version, these fields were as follows: 
    # user = models.ForeignKey('UserAccess', null=False, editable=False, related_name='u2ugp',
    #                          help_text='user to be granted privilege')
    # group = models.ForeignKey('GroupAccess', null=False, editable=False, related_name='g2ugp',
    #                           help_text='group to which privilege applies')
    # grantor = models.ForeignKey('UserAccess', null=False, editable=False, related_name='x2ugp',
    #                             help_text='grantor of privilege')

    user = models.ForeignKey(User,
                             null=False,
                             editable=False,
                             related_name='u2ugp',
                             help_text='user to be granted privilege')

    group = models.ForeignKey(Group,
                              null=False,
                              editable=False,
                              related_name='g2ugp',
                              help_text='group to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=False,
                                editable=False,
                                related_name='x2ugp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = ('user', 'group', 'grantor')


class UserResourcePrivilege(models.Model):
    """ Privileges of a user over a resource

    This model encodes privileges of individual users, like an access
    control list; see GroupResourcePrivilege and UserGroupPrivilege
    for other kinds of privilege.
    """

    privilege = models.IntegerField(choices=PrivilegeCodes.PRIVILEGE_CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    start = models.DateTimeField(editable=False, auto_now=True)

    # in the prior version, these fields were as follows: 
    # user = models.ForeignKey('UserAccess', null=False, editable=False,
    #                          related_name='u2urp',
    #                          help_text='user to be granted privilege')
    # resource = models.ForeignKey('ResourceAccess', null=False, editable=False,
    #                              related_name="r2urp",
    #                              help_text='resource to which privilege applies')
    # grantor = models.ForeignKey('UserAccess', null=False, editable=False,
    #                             related_name='x2urp',
    #                             help_text='grantor of privilege')

    user = models.ForeignKey(User, 
                             null=False, 
                             editable=False,
                             related_name='u2urp',
                             help_text='user to be granted privilege')

    resource = models.ForeignKey(BaseResource, 
                                 null=False, 
                                 editable=False,
                                 related_name='r2urp',
                                 help_text='resource to which privilege applies')

    grantor = models.ForeignKey(User, 
                                null=False, 
                                editable=False,
                                related_name='x2urp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = ('user', 'resource', 'grantor')


class GroupResourcePrivilege(models.Model):
    """ Privileges of a group over a resource.

    The group privilege over a resource is never meaningful;
    it is resolved instead into user privilege for each member of
    the group, as listed in UserGroupPrivilege above.
    """

    privilege = models.IntegerField(choices=PrivilegeCodes.PRIVILEGE_CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    start = models.DateTimeField(editable=False, auto_now=True)

    # Prior to this version, the following structure was used. 
    # group = models.ForeignKey('GroupAccess', null=False, editable=False,
    #                           related_name='g2grp',
    #                           help_text='group to be granted privilege')
    # resource = models.ForeignKey('ResourceAccess', null=False, editable=False,
    #                              related_name='r2grp',
    #                              help_text='resource to which privilege applies')
    # grantor = models.ForeignKey('UserAccess', null=False, editable=False,
    #                             related_name='x2grp',
    #                             help_text='grantor of privilege')

    group = models.ForeignKey(Group, 
                              null=False, 
                              editable=False,
                              related_name='g2grp',
                              help_text='group to be granted privilege')

    resource = models.ForeignKey(BaseResource,
                                 null=False,
                                 editable=False,
                                 related_name='r2grp',
                                 help_text='resource to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=False,
                                editable=False,
                                related_name='x2grp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = ('group', 'resource', 'grantor')


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

    @property
    def held_resources(self):
        """ Workalike for many-to-many relationship

        :return: QuerySet of BaseResource held by user

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

	return BaseResource.objects.filter(r2urp__user=self.user)

    @property
    def held_groups(self):
        """ Workalike for many-to-many relationship

        :return: QuerySet of Group held by user

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

	return Group.objects.filter(g2ugp__user=self.user) 

    ##########################################
    # PUBLIC METHODS: groups
    ##########################################

    def create_group(self, title):
        """
        Create a group.

        :param title: Group title.
        :return: Group object

        Anyone can create a group. The creator is also the first owner.

        An owner can assign ownership to another user via share_group_with_user,
        but cannot remove self-ownership if that would leave the group with no
        owner.
        """
	if __debug__: 
	    assert isinstance(title, basestring) 

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        raw_group = Group.objects.create(name=title) # the single attribute of the group
        access_group = GroupAccess.objects.create(group=raw_group)
        raw_user = self.user
        # Must bootstrap access control system initially
        UserGroupPrivilege.objects.create(group=raw_group,
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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser or self.owns_group(this_group):
	    # THE FOLLOWING ARE UNNECESSARY due to delete cascade. 
            # UserGroupPrivilege.objects.filter(group=this_group).delete()
            # GroupResourcePrivilege.objects.filter(group=this_group).delete()
            # access_group.delete()

            this_group.delete()
        else:
            raise PermissionDenied("User must own group")

    ################################
    # held and owned groups
    ################################

    def get_held_groups(self):
        """ DEPRECATED: Get number of groups accessible to self. Use code below instead

        :return: QuerySet evaluating to held groups.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")
	# TODO: deprecate held_groups, copy code here
        return self.held_groups

    def get_number_of_held_groups(self):
        """ 
        DEPRECATED: use explicit count(). Get number of groups held by self.

        :return: Integer number of held groups.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.held_groups.count()

    def get_owned_groups(self):
        """
        Return a list of groups owned by self.

        :return: QuerySet of groups owned by self.

        Usage:
        ------

        Because this returns a QuerySet, and not a set of objects, one can append
        extra QuerySet attributes to it, e.g. ordering, selection, projection:

            q = user.get_owned_groups()
            q2 = q.order_by(...)
            v2 = q2.values('title')
            # etc

        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return Group.objects.filter(g2ugp__user=self.user,
                                    g2ugp__privilege=PrivilegeCodes.OWNER)

    def get_number_of_owned_groups(self):
        """
        DEPRECATED: iuse explicit count() instead. Get number of groups owned by current user

        :return: Integer
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.get_owned_groups().count()

    #################################
    # access checks for groups
    #################################

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        if UserGroupPrivilege.objects.filter(group=this_group,
                                             privilege=PrivilegeCodes.OWNER,
                                             user=self.user).exists():
            return True
        else:
            return False

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser:
            return True

        if UserGroupPrivilege.objects.filter(group=this_group,
                                             privilege__lte=PrivilegeCodes.CHANGE,
                                             user=self.user).exists():
            return True
        else:
            return False

    # TODO: should an inactive group be viewable?
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
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser or access_group.public:
            return True

        if UserGroupPrivilege.objects.filter(group=this_group,
                                             privilege__lte=PrivilegeCodes.VIEW,
                                             user=self.user).exists():
            return True
        else:
            return False

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if access_group.discoverable or access_group.public:
            return True
        else:
            return self.can_view_group(this_group)

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_group(this_group)

    ####################################
    # sharing permission checking
    ####################################

    def can_share_group(self, this_group, this_privilege):
        """
        Return True if a given user can share this group with a given privilege.

        :param this_group: group to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible, otherwise false.

        This determines whether the current user can share a group, independent of
        what entity it might be shared with.

        Usage:
        ------

            if my_user.can_share_group(some_group, PrivilegeCodes.VIEW):
                # ...time passes, forms are created, requests are made...
                my_user.share_group_with_user(some_group, some_user, PrivilegeCodes.VIEW)

        In practice:
        ------------

        If this returns False, UserAccess.share_group_with_user will raise an exception
        for the corresponding arguments -- *guaranteed*.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser:
            return True

        if not self.owns_group(this_group) and not access_group.shareable:
            return False

        # must have a this_privilege greater than or equal to what we want to assign
        if UserGroupPrivilege.objects.filter(group=this_group,
                                             user=self.user,
                                             privilege__lte=this_privilege).exists():
            return True
        else:
            return False

    ####################################
    # group membership sharing
    ####################################

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

        "can_share_group" is used to construct views with appropriate buttons or popups, e.g., "share with...",
        while "share_group_with_user" is used in the form responder to implement changes.
        This is safe to do even if the state changes, because "share_group_with_user" always
        rechecks permissions before implementing changes. If -- in the interim -- one removes
        _my_user_'s sharing privileges, _share_group_with_user_ will raise an exception.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        # check for user authorization
        if not self.owns_group(this_group) and not access_group.shareable and not self.user.is_superuser:
            raise PermissionDenied("User is not group owner and group is not shareable")

        # must have a privilege greater than or equal to what we want to assign
        if not self.user.is_superuser and not UserGroupPrivilege.objects.filter(group=this_group,
                                                                                user=self.user,
                                                                                privilege__lte=this_privilege):
            raise PermissionDenied("User has insufficient privilege over group")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
	with transaction.atomic(): 
	    record, created = UserGroupPrivilege.objects.get_or_create(group=this_group,
								       user=this_user,
								       grantor=self.user,
								       defaults = { 'privilege' : this_privilege })
	    if not created:
		if record.privilege==PrivilegeCodes.OWNER \
			and this_privilege!=PrivilegeCodes.OWNER \
			and access_group.get_owners().count()==1:
		    raise PermissionDenied("Cannot remove last owner of group")
		record.privilege=this_privilege
		record.save()

        # owner overrides all lesser privilege
        if self.owns_group(this_group) or self.user.is_superuser:
            UserGroupPrivilege.objects\
                              .filter(group=this_group,
                                      user=this_user,
                                      privilege__lt=this_privilege)\
                              .all()\
                              .delete()

    def __handle_unshare_group_with_user(self, this_group, this_user, command=CommandCodes.CHECK):
        """
        PRIVATE: routine that combines check for privilege with setting of privilege.

        :param this_group: group to unshare.
        :param this_user:  user with which to unshare it.
        :param command: whether to do the command or check whether it is possible.
        :return: None

        This routine is a helper that combines the code for checking permission and doing actions.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)
            assert command == CommandCodes.CHECK or command == CommandCodes.DO

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        if this_user not in this_group.gaccess.members.all():
            if command == CommandCodes.DO:
                raise PermissionDenied("User is not a member of the group")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of group
        #   Modifying privileges for self
        if self.user.is_superuser \
            or self.owns_group(this_group) \
            or this_user == self.user:
            # if there is a different owner,  we're fine
            if UserGroupPrivilege.objects.filter(group=this_group,
                                                 privilege=PrivilegeCodes.OWNER).exclude(user=this_user).exists():
                if command == CommandCodes.DO:
                    # then remove the record.
                    # this does not return an error if the object is not shared with the user
                    UserGroupPrivilege.objects.filter(group=this_group,
                                                      user=this_user)\
                                      .delete()
                return True  #  report success!

            else:
                # Hidden privilege other than OWNER cannot be removed for OWNERS
                if command == CommandCodes.DO:
                    raise PermissionDenied("Cannot remove sole owner of group")
                else:
                    return False
        else:
            if command == CommandCodes.DO:
                raise PermissionDenied("User has insufficient privilege to unshare")
            else:
                return False

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_unshare_group_with_user(this_group, this_user, CommandCodes.DO)

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
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_unshare_group_with_user(this_group, this_user, CommandCodes.CHECK)

    def __handle_undo_share_group_with_user(self, this_group, this_user, command=CommandCodes.CHECK, this_grantor=None):
	""" private handler for undoing share groups """

        access_group = this_group.gaccess

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None:
            if not UserGroupPrivilege.objects.filter(group=this_group,
                                                     user=this_user,
                                                     grantor=this_grantor):
                if command == CommandCodes.DO:
                    raise PermissionDenied("Grantor did not grant privilege")
                else:
                    return False

            if not self.owns_group(this_group) and not self.user.is_superuser:
                if command == CommandCodes.DO:
                    raise PermissionDenied("Self must be owner or admin")
                else:
                    return False

        if this_user not in access_group.members.all():
            if command == CommandCodes.DO:
                raise PermissionDenied("User is not a member of the group")
            else:
                return False
        try:
            existing = UserGroupPrivilege.objects.get(group=this_group,
                                                      user=this_user,
                                                      grantor=self.user)
            # if the privilege for user is not OWNER,
            # or there's another OWNER:
            if existing.privilege != PrivilegeCodes.OWNER \
                    or UserGroupPrivilege.objects \
                          .filter(group=this_group,
                                  privilege=PrivilegeCodes.OWNER) \
                          .exclude(user=this_user, grantor=this_grantor):
                if command == CommandCodes.DO:
                    # then remove the record.
                    # this does not return an error if the object is not shared with the user
                    UserGroupPrivilege.objects.filter(group=this_group,
                                                      user=this_user,
                                                      grantor=this_grantor).delete()
                return True
            else:
                if command == CommandCodes.DO:
                    raise PermissionDenied("Cannot remove sole owner of group")
                else:
                    return False
        except UserGroupPrivilege.DoesNotExist:
            if command == CommandCodes.DO:
                raise PermissionDenied("No share to undo")
            else:
                return False

    def undo_share_group_with_user(self, this_group, this_user, this_grantor=None):
        """
        Remove a user from a group who was assigned by self.

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

        "can_undo_share_*" is used to construct views with appropriate forms and
        change buttons, while "undo_share_*" is used to implement the responder to the
        view's forms. "undo_share_*" still checks for permission (again) in case
        things have changes (e.g., through a stale form).
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)
            assert this_grantor is None or isinstance(this_grantor, User)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_group_with_user(this_group, this_user, CommandCodes.DO, this_grantor)

    def can_undo_share_group_with_user(self, this_group, this_user, this_grantor=None):
        """
        Check whether we can remove a user from a group who was assigned by self.

        :param this_group: group to affect.
        :param this_user: user with whom to unshare group.
        :return: Boolean

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
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)
            assert isinstance(this_user, User)
            assert this_grantor is None or isinstance(this_grantor, User)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_group_with_user(this_group, this_user, CommandCodes.CHECK, this_grantor)

    ##########################################
    # users whose access could be undone by self
    ##########################################
    def get_group_undo_users(self, this_group):
        """
        Get a list of users to whom self granted access

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
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser or self.owns_group(this_group):

            if access_group.get_owners().count()>1:
                # every possible undo is permitted, including self-undo
                return User.objects.filter(is_active=True, 
					   u2ugp__group=this_group) 
            else:  
		# exclude sole owner from undo
                return User.objects.filter(is_active=True, 
					   u2ugp__group=this_group)\
                                   .exclude(pk__in=User.objects.filter(is_active=True, 
								       u2ugp__group=this_group,
                                                                       u2ugp__privilege=PrivilegeCodes.OWNER))
        else:
            if this_group.gaccess.get_owners().count()>1:
                return User.objects.filter(is_active=True, 
					   u2ugp__grantor=self.user,
                                           u2ugp__group=this_group)

            else:  # exclude sole owner from undo
                # The exclude subquery avoids possible many-to-many anomalies in exclude (in which the
                # phrases for u2ugp are treated as separate rather than combined).
                return User.objects.filter(is_active=True, 
					   u2ugp__group=this_group,
                                           u2ugp__grantor=self.user)\
                                   .exclude(pk__in=User.objects.filter(is_active=True, 
								       u2ugp__group=this_group,
                                                                       u2ugp__grantor=self.user,
                                                                       u2ugp__privilege=PrivilegeCodes.OWNER))

    def get_group_unshare_users(self, this_group):
        """
        Get a list of users who could be unshared from this group.

        :param this_group: group to check.
        :return: list of users who could be removed by self.

        A user can be unshared with a group if:

            * The user is self

            * Self is group owner.

            * Self has admin privilege.

        except that a user in the list cannot be the last owner of the group.

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

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if self.user.is_superuser or self.owns_group(this_group):
            # everyone who holds this resource, minus potential sole owners
            if access_group.get_owners().count() == 1:
                # get list of owners to exclude from main list
		# This should be one user but can be two due to race conditions. 
		# Avoid races by excluding action in that case. 
                ids_exclude = User.objects.filter(is_active=True, 
						  u2ugp__group=this_group, 
				                  u2ugp__privilege=PrivilegeCodes.OWNER)
                return access_group.get_members().exclude(pk__in=ids_exclude)
            else:
                return access_group.get_members()
        elif self in access_group.holding_users.all():
            if access_group.get_owners().count() == 1:
                # if I'm not that owner
		# TODO: replace with query to API to pick up active flag
                if not UserGroupPrivilege.objects\
                        .filter(user=self.user, group=this_group, privilege=PrivilegeCodes.OWNER):
                    # this is a fancy way to return self as a QuerySet
                    return User.objects.filter(uaccess=self)
                else:
                    # I can't remove anyone
                    return User.objects.none()
        else:
            return User.objects.none()

    ##########################################
    # PUBLIC FUNCTIONS: resources
    ##########################################

    ##########################################
    # held and owned resources
    ##########################################

    def get_held_resources(self):
        """
        Get a list of resources held by user.

        :return: List of resource objects accessible (in any form) to user.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return BaseResource.objects.filter(Q(r2urp__user=self.user) | Q(r2grp__group__g2ugp__user=self.user))

    def get_number_of_held_resources(self):
        """
        DEPRECATED: Invoke count directly. Get the number of resources held by user.

        :return: Integer number of resources accessible for this user.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return BaseResource.objects.filter(Q(r2urp__user=self.user)
                                         | Q(r2grp__group__g2ugp__user=self.user)).count()

    def get_owned_resources(self):
        """
        Get a list of resources owned by user.

        :return: List of resource objects owned by this user.
        """

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")
	return BaseResource.objects.filter(r2urp__user=self.user,
					   r2urp__privilege=PrivilegeCodes.OWNER)

    def get_number_of_owned_resources(self):
        """
        DEPRECATED: invoke count() directly. Get number of resources owned by self.

        :return: Integer number of resources owned by user.

        This is a separate procedure, rather than get_owned_resources().count(), due to performance concerns.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.get_owned_resources().count()

    def get_editable_resources(self):
        """
        Get a list of resources that can be edited by user.

        :return: List of resource objects that can be edited  by this user.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

	return BaseResource.objects.filter(r2urp__user=self.user, raccess__immutable=False,
                                           r2urp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    def get_resources_with_explicit_access(self, this_privilege):
        """
        Get a list of resources that the user has the specified privilege
        Args:
            this_privilege: one of the PrivilegeCodes

        Returns: list of resource objects (QuerySet)

	Note: One must check the immutable flag if privilege < VIEW.
        """
	if __debug__: 
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

	selected =  BaseResource.objects\
				.filter(r2urp__user=self.user, 
					r2urp__privilege=this_privilege)\
				.exclude(id__in=BaseResource.objects\
							    .filter(r2urp__user=self.user,
								    r2urp__privilege__lt=this_privilege))
	if this_privilege < PrivilegeCodes.VIEW: 
	    return selected.filter(raccess__immutable=False) 
	else:
	    return selected

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
        explicitly, using UserAccess.can_change_resource()
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

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
        Note that the ability to change a resource is not just contingent upon sharing,
        but also upon the resource flag "immutable". Thus "owns" does not imply "can change" privilege.
        Note also that the ability to change a resource applies to its data and metadata, but not to its
        resource state flags: shareable, public, immutable, published, and discoverable.
        We elected not to return a queryset for this one, because that would mean that it
        would return two types depending upon conditions -- Boolean for simple queries and
        QuerySet for complex queries.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if access_resource.immutable:
            return False

        if self.user.is_superuser:
            return True

        if UserResourcePrivilege.objects.filter(resource=this_resource,
                                                privilege__lte=PrivilegeCodes.CHANGE,
                                                user=self.user).exists():
            return True

        if GroupResourcePrivilege.objects.filter(resource=this_resource,
                                                 privilege__lte=PrivilegeCodes.CHANGE,
                                                 group__g2ugp__user=self.user).exists():
            return True

        return False

    def can_change_resource_flags(self, this_resource):
        """
        Whether self can change resource flags.

        :param this_resource: Resource to check.
        :return: True if user can set flags otherwise false.

        This is not enforced. It is up to the programmer to obey this restriction.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_resource(this_resource)

    def can_view_resource(self, this_resource):
        """
        Whether user can view this resource

        :param this_resource: Resource to check
        :return: True if user can view this resource, otherwise false.

        Note that one can view resources that are public, that one does not own.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if access_resource.public:
            return True

        if self.user.is_superuser:
            return True

        if UserResourcePrivilege.objects.filter(resource=this_resource,
                                                privilege__lte=PrivilegeCodes.VIEW,
                                                user=self.user).exists():
            return True

        if GroupResourcePrivilege.objects.filter(resource=this_resource,
                                                 privilege__lte=PrivilegeCodes.VIEW,
                                                 group__g2ugp__user=self.user).exists():
            return True

        return False

    def can_delete_resource(self, this_resource):
        """
        Whether user can delete a resource

        :param this_resource: Resource to check.
        :return: True if user can delete the resource, otherwise false.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.user.is_superuser or self.owns_resource(this_resource)

    ##########################################
    # check sharing rights
    ##########################################

    def can_share_resource(self, this_resource, this_privilege):
        """
        Can a resource be shared by the current user?

        :param this_resource: resource to check
        :param this_privilege: privilege to assign
        :return: Boolean: whether resource can be shared.

        In this computation, user target of sharing is not relevant.
        One can share with self, which can only downgrade privilege.
        """
        # translate into ResourceAccess object
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        # access control logic: Can change privilege if
        #   Admin
        #   Owner
        #   Privilege for self
        whom_priv = access_resource.get_combined_privilege(self.user)

        # check for user authorization
        if self.user.is_superuser:
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

    def can_share_resource_with_group(self, this_resource, this_group, this_privilege):
        """
        Check whether one can share a resource with a group.

        :param this_resource: resource to share.
        :param this_group: group with which to share it.
        :param this_privilege: privilege level of sharing.
        :return: Boolean: whether one can share.

        This function returns False exactly when share_resource_with_group will raise
        an exception if called.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        if this_privilege==PrivilegeCodes.OWNER:
            return False

        # check for user authorization
        # a) user must have privilege over resource
        # b) user must be in the group
        if not self.can_share_resource(this_resource, this_privilege):
            return False

        if self.user not in this_group.gaccess.get_members() and not self.user.is_superuser:
            return False

        return True

    def __handle_undo_share_resource_with_group(self, this_resource, this_group, command=CommandCodes.CHECK,
                                                this_grantor=None):
        """ Multi-model undo of sharing a resource with a group.

        :param this_resource:  resource to unshare
        :param this_group: group with which to unshare it.
        :param command: Whether to CHECK or DO
        :param this_grantor: grantor of privilege
        :return: None
        """
        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is None:
            this_grantor = self.user

        if not self.owns_resource(this_resource) and not self.user.is_superuser:
            if command == CommandCodes.DO:
                raise PermissionDenied("Self must be owner or admin")
            else:
                return False  # non-owners cannot specify grantor

        if not GroupResourcePrivilege.objects.filter(group=this_group,
                                                     resource=this_resource,
                                                     grantor=this_grantor).exists():

            if command == CommandCodes.DO:
                raise PermissionDenied("No privilege to remove")
            else:
                return False

        if GroupResourcePrivilege.objects.filter(resource=this_resource,
                                                 group=this_group,
                                                 grantor=this_grantor).exists():
            if command == CommandCodes.DO:
                GroupResourcePrivilege.objects.get(resource=this_resource,
                                                   group=this_group,
                                                   grantor=this_grantor)\
					      .delete()
            return True  # return success
        else:
            if command == CommandCodes.DO:
                raise PermissionDenied("Grantor did not grant privilege")
            else:
                return False

    def undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        """
        Remove resource privileges self-granted to a group.

        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: None

        This tries to remove one user access record for "this_group" and "this_resource"
        if grantor is self. If this_grantor is specified, that is utilized as grantor as long as
        self is owner or admin.
        """
	if __debug__: 
	    assert isinstance(this_resource, BaseResource)
	    assert isinstance(this_group, Group)
            assert this_grantor is None or isinstance(this_grantor, User)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_resource_with_group(this_resource,
                                                            this_group,
                                                            CommandCodes.DO,
                                                            this_grantor)

    def can_undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        """
        Check whether one can remove resource privileges self-granted to a group.

        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: Boolean

        This checks whether one can remove one user access record for "this_group" and "this_resource"
        if grantor is self. If this_grantor is specified, that is utilized as the grantor as long as
        self is owner or admin.
        """
	if __debug__: 
	    assert isinstance(this_resource, BaseResource)
	    assert isinstance(this_group, Group)
            assert this_grantor is None or isinstance(this_grantor, User)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_resource_with_group(this_resource,
                                                            this_group,
                                                            CommandCodes.CHECK,
                                                            this_grantor)

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

        Assigning user (self) must be admin, owner, or have equivalent privilege over resource.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)
            assert isinstance(this_resource, BaseResource)
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        # access control logic: Can change privilege if
        #   Admin
        #   Self-set permission
        #   Owner
        #   Non-owner and shareable
        whom_priv = access_resource.get_combined_privilege(self.user)
        grantee_priv = access_resource.get_combined_privilege(this_user)

        # check for user authorization
        if self.user.is_superuser:
            pass  # admin can do anything

        elif whom_priv == PrivilegeCodes.OWNER:
            pass  # owner can do anything

        elif access_resource.shareable:
            pass  # non-owners can share

        else:
            raise PermissionDenied("User must own resource or have sharing privilege")

        # privilege checking

        if whom_priv > PrivilegeCodes.VIEW:
            raise PermissionDenied("User has no privilege over resource")

        if whom_priv > this_privilege:
            raise PermissionDenied("User has insufficient privilege over resource")

        # non owner can't downgrade privilege granted by someone else
        # grantee_priv: current privilege of the grantee (this_user)
        # this_privilege: proposed privilege for the grantee (this_user)
        if whom_priv != PrivilegeCodes.OWNER and grantee_priv < this_privilege:
            record = UserResourcePrivilege.objects.get(resource=this_resource,
                                                       user=this_user,
                                                       privilege=grantee_priv)

            # current grantor (self) is not the same as the original grantor
            if record.grantor != self.user:
                raise PermissionDenied("User has insufficient privilege over resource")

        # This logic implicitly limits one to one record per resource and requester.
        with transaction.atomic():
            record, create = UserResourcePrivilege.objects.get_or_create(resource=this_resource,
                                                                 user=this_user,
                                                                 grantor=self.user,
                                                                 defaults = {'privilege': this_privilege})
            if record.privilege == PrivilegeCodes.OWNER \
                    and this_privilege != PrivilegeCodes.OWNER \
                    and access_resource.get_owners().count() == 1:
                raise PermissionDenied("Cannot remove last owner of resource")

            if not create:
                record.privilege = this_privilege
                record.save()

        # if there exist higher privileges than what was granted now 
        # (this_privilege) then those needs to be deleted
        if self.user.is_superuser or self.owns_resource(this_resource):
            UserResourcePrivilege.objects.filter(resource=this_resource,
                                                 user=this_user,
                                                 privilege__lt=this_privilege)\
                                 .all()\
                                 .delete()

    def __handle_unshare_resource_with_user(self, this_resource, this_user, command=CommandCodes.CHECK):

        """
        Remove a user from a resource by removing privileges.

        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :param command: command code to perform
        :return: Boolean if command is CommandCodes.CHECK, otherwise none

        This removes a user "this_user" from resource access to "this_resource" if one of the following is true:
            * self is an administrator.
            * self owns the group.
            * requesting user is the grantee of resource access.
        *and* removing the user will not lead to a resource without an owner.
        There is no provision for revoking lower-level permissions for an owner.
        If a user is a sole owner and holds other privileges, this call will not remove them.
        """

        access_user = this_user.uaccess
        access_resource = this_resource.raccess

        if this_user not in access_resource.holding_users.all():
            if command == CommandCodes.DO:
                raise PermissionDenied("User does not have access to resource")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of resource
        #   Modifying self
        if self.user.is_superuser \
                or access_resource.get_combined_privilege(self.user) == PrivilegeCodes.OWNER \
                or access_user == self:
            # if there is some other owner
            if UserResourcePrivilege.objects \
                    .filter(resource=this_resource,
                            privilege=PrivilegeCodes.OWNER) \
                    .exclude(user=this_user)\
                    .exists():
                # then remove the record.
                # this does not return an error if the object is not shared with the user
                if command == CommandCodes.DO:
                    UserResourcePrivilege.objects.filter(resource=this_resource,
                                                         user=this_user).delete()
                return True  # indicate success
            else:
                # this prevents one from removing privilege for a user
                # if any grant is owner. This protects the other grants as well.
                if command == CommandCodes.DO:
                    raise PermissionDenied("Cannot remove sole resource owner")
                else:
                    return False
        else:
            if command == CommandCodes.DO:
                raise PermissionDenied("Insufficient privilege to unshare resource")
            else:
                return False

    def unshare_resource_with_user(self, this_resource, this_user):
        """
        Unshare a resource with a specific user, removing all privilege for that user

        :param this_resource: Resource to unshare
        :param this_user:  User wich whom to unshare it.
        :return: True if it is unshared successfully, otherwise false
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_unshare_resource_with_user(this_resource, this_user, CommandCodes.DO)

    def can_unshare_resource_with_user(self, this_resource, this_user):
        """
        Check whether one can dissociate a specific user from a resource

        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether one can unshare this resource with this user.

        This checks if both of the following are true:
            * self is administrator, or owns the resource.
            * This act does not remove the last owner of the resource.
        If so, it removes all privilege over this_resource for this_user.
        To remove a single privilege, rather than all privilege,
        see can_undo_share_resource_with_user
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")
        return self.__handle_unshare_resource_with_user(this_resource, this_user, CommandCodes.CHECK)

    def __handle_undo_share_resource_with_user(self, this_resource, this_user, command=CommandCodes.CHECK,
                                               this_grantor=None):
        """
        Remove a self-granted privilege from a user.

        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :return: Boolean if command is CommandCodes.CHECK, otherwise none

        This removes a user "this_user" from resource access to "this_resource" if self granted the privilege,
        *and* removing the user will not lead to a resource without an owner.
        """

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None:
            if not GroupResourcePrivilege.objects.filter(user=this_user,
                                                         resource=this_resource,
                                                         grantor=this_grantor).exists():
                if command == CommandCodes.DO:
                    raise PermissionDenied("Grantor did not grant privilege")
                else:
                    return False

            if not self.owns_resource(this_resource) and not self.user.is_superuser:
                if command == CommandCodes.DO:
                    raise PermissionDenied("Self must be owner or admin")
                else:
                    return False
        else:
            this_grantor = self.user

        try:
            existing = UserResourcePrivilege.objects.get(resource=this_resource,
                                                         user=this_user,
                                                         grantor=this_grantor)
            # if there is an owner other than the grantee, or the grantee is not an owner
            if existing.privilege != PrivilegeCodes.OWNER \
                    or UserResourcePrivilege.objects\
                                            .filter(resource=this_resource,
                                                    privilege=PrivilegeCodes.OWNER)\
                                            .exclude(resource=this_resource,
                                                     user=this_user).exists():
                # then remove the record.
                # this does not return an error if the object is not shared with the user
                if command == CommandCodes.DO:
                    UserResourcePrivilege.objects.filter(resource=this_resource,
                                                         user=this_user,
                                                         grantor=this_grantor).delete()
                return True  # Indicate success!

            else:
                # this prevents one from removing privilege for a user
                # if any grant is owner. This protects the other grants as well.
                if command == CommandCodes.DO:
                    raise PermissionDenied("Cannot remove sole resource owner")
                else:
                    return False

        except UserResourcePrivilege.DoesNotExist:
            if command == CommandCodes.DO:
                raise PermissionDenied("No share to undo")
            else:
                return False

    def undo_share_resource_with_user(self, this_resource, this_user, this_grantor=None):
	""" Undo a previous share by the same user """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_resource_with_user(this_resource, 
							   this_user, 
						           CommandCodes.DO, 
							   this_grantor)

    def can_undo_share_resource_with_user(self, this_resource, this_user, this_grantor=None):
        """
        Check whether one can dissociate a specific user from a resource

        :param this_resource: resource to protect.
        :param this_user: user to remove.
        :return: Boolean: whether one can unshare this resource with this user.

        This checks if both of the following are true:

            * self is administrator, or owns the resource.

            * This act does not remove the last owner of the resource.

        If so, it removes all privilege over this_resource for this_user.
        To remove a single privilege, rather than all privilege,
        see can_undo_share_resource_with_user
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_undo_share_resource_with_user(this_resource, this_user, CommandCodes.CHECK, this_grantor)

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
	    assert this_privilege >= PrivilegeCodes.OWNER and this_privilege <= PrivilegeCodes.VIEW

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_group = this_group.gaccess

        if this_privilege==PrivilegeCodes.OWNER:
            raise PermissionDenied("Groups cannot own resources")
        if this_privilege<PrivilegeCodes.OWNER or this_privilege>PrivilegeCodes.VIEW:
            raise PermissionDenied("Privilege level not valid")

        # check for user authorization
        if not self.can_share_resource(this_resource, this_privilege):
            raise PermissionDenied("User has insufficient sharing privilege over resource")

        if self.user not in access_group.members.all() and not self.user.is_superuser:
            raise PermissionDenied("User is not a member of the group and not an admin")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        with transaction.atomic():  # get_or_create observed to be non-atomic in testing..
            record, created = GroupResourcePrivilege.objects.get_or_create(resource=this_resource,
                                                                           group=this_group,
                                                                           grantor=self.user,
                                                                           defaults = { 'privilege': this_privilege })

            # record.start=timezone.now() # now automatically set
            if not created:
                # no need to check for owner privilege; impossible
                record.privilege=this_privilege
                record.save()

        # owner overrides all lesser privilege
        if self.owns_group(this_group) or self.user.is_superuser:
            # print('invoking override for privileges < ', this_privilege)
            GroupResourcePrivilege.objects\
                              .filter(group=this_group,
                                      resource=this_resource,
                                      privilege__lt=this_privilege)\
                              .all()\
                              .delete()


    def __handle_unshare_resource_with_group(self, this_resource, this_group, command=CommandCodes.CHECK):

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_group, Group)
            assert command == CommandCodes.CHECK or command == CommandCodes.DO

        access_resource = this_resource.raccess

        if this_group not in access_resource.holding_groups.all():
            if command == CommandCodes.DO:
                raise PermissionDenied("Group does not have access to resource")
            else:
                return False

        # User authorization: can make change if
        #   Admin
        #   Owner of resource
        #   Owner of group
        if self.user.is_superuser \
        or self.owns_resource(this_resource) \
        or self.owns_group(this_group):

            # this does not return an error if the object is not shared with the user
            if command == CommandCodes.DO:
                GroupResourcePrivilege.objects.filter(resource=this_resource,
                                                      group=this_group).delete()
            return True

        else:
            if command == CommandCodes.DO:
                raise PermissionDenied("Insufficient privilege to unshare resource")
            else:
                return False

    def unshare_resource_with_group(self, this_resource, this_group):
        """
        Remove a group from access to a resource by removing privileges.

        :param this_resource: resource to be affected.
        :param this_group: user with which to unshare resource
        :return: None

        This removes a user "this_group" from access to "this_resource" if one of the following is true:
            * self is an administrator.
            * self owns the resource.
            * self owns the group.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        return self.__handle_unshare_resource_with_group(this_resource, this_group, CommandCodes.DO)

    def can_unshare_resource_with_group(self, this_resource, this_group):
        """
        Check whether one can unshare a resource with a group.

        :param this_resource: resource to be protected.
        :param this_group: group with which to unshare resource.
        :return: Boolean

        Unsharing will remove a user "this_group" from access to "this_resource" if one of the following is true:
            * self is an administrator.
            * self owns the resource.
            * self owns the group.
        This routine returns False exactly when unshare_resource_with_group will raise an exception.
        """
	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")
        return self.__handle_unshare_resource_with_group(this_resource, 
							 this_group, 
						         CommandCodes.CHECK)

    ##########################################
    # users whose access could be undone by self
    ##########################################
    def get_resource_undo_users(self, this_resource):
        """
        Get a list of users to whom self granted access

        :param this_resource: resource to check.
        :return: list of users granted access by self.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if self.user.is_superuser or self.owns_resource(this_resource):

            if access_resource.get_owners().count() > 1:
                # print("Returning results for all undoes -- owners>1")
                return User.objects.filter(is_active=True, 
					   u2urp__resource=this_resource)
            else:  # exclude sole owner from undo
                # print("Returning results for non-owner undos -- owners==1")
                # We need to return the users who are not owners, not the users who have privileges other than owner
                # all candidate undos
                ids_owner = User.objects.filter(is_active=True, 
					        u2urp__resource=this_resource,
                                                u2urp__privilege=PrivilegeCodes.OWNER)
                # return difference
                return User.objects.filter(is_active=True, 
				           u2urp__resource=this_resource)\
                                   .exclude(pk__in=ids_owner)
        else: # rules for non-owners
            if access_resource.get_owners().count()>1:
                # self is grantor
                return User.objects.filter(is_active=True, 
				           u2urp__grantor=self.user,
					   u2urp__resource=this_resource)

            else:  # exclude sole owner from undo
                # The exclude subquery avoids possible many-to-many anomalies in exclude (in which the
                # phrases for u2urp are treated as separate rather than combined).
                return User.objects.filter(is_active=True, 
					   u2urp__grantor=self.user,
                                           u2urp__resource=this_resource)\
                                   .exclude(pk__in=User.objects.filter(is_active=True, 
								       u2urp__grantor=self.user,
                                                                       u2urp__resource=this_resource,
                                                                       u2urp__privilege=PrivilegeCodes.OWNER))

    def get_resource_unshare_users(self, this_resource):
        """
        Get a list of users who could be unshared from this resource.

        :param this_resource: resource to check.
        :return: list of users who could be removed by self.
        """
        # Users who can be removed fall into three catagories
        # a) self is admin: everyone.
        # b) self is resource owner: everyone.
        # c) self is beneficiary: self only

        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        access_resource = this_resource.raccess

        if self.user.is_superuser or self.owns_resource(this_resource):
            # everyone who holds this resource, minus potential sole owners
            if access_resource.get_owners().count() == 1:
                # get list of owners to exclude from main list
		# this should be one user but could be more than one 
		# due to race conditions. To make code more robust, 
 		# exclude action in this case 
                ids_exclude = User.objects.filter(is_active=True, 
						  u2urp__resource=this_resource, 
						  u2urp__privilege=PrivilegeCodes.OWNER)
                return access_resource.get_users().exclude(pk__in=ids_exclude)
            else:
                return access_resource.get_users()
        elif self in access_resource.holding_users.all():
            return User.objects.none()
        else:
            return User.objects.none()

    def get_resource_undo_groups(self, this_resource):
        """
        Get a list of groups to whom self granted access

        :param this_resource: resource to check.
        :return: list of groups granted access by self.

        A user can undo a privilege if
            1. That privilege was assigned by this user.
            2. User owns the resource
            3. User owns the group -- *not implemented*
            4. User is an administrator
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")

        if self.user.is_superuser or self.owns_resource(this_resource):
            return Group.objects.filter(g2grp__resource=this_resource)
        else:  #  privilege only for grantor
            return Group.objects.filter(g2grp__resource=this_resource,
                                        g2grp__grantor=self.user)

    def get_resource_unshare_groups(self, this_resource):
        """
        Get a list of groups who could be unshared from this group.

        :param this_resource: resource to check.
        :return: list of groups who could be removed by self.

        This is a list of groups for which unshare_resource_with_group will work for this user.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

	if not self.user.is_active: raise PermissionDenied("Requesting user is not active")
        # Users who can be removed fall into three categories
        # a) self is admin: everyone with access.
        # b) self is resource owner: everyone with access.
        # c) self is group owner: only for owned groups

        if self.user.is_superuser or self.owns_resource(this_resource):
            # all shared groups
            return Group.objects.filter(g2grp__resource=this_resource)
        else:
            return Group.objects.filter(g2ugp__user=self.user,
                                        g2ugp__privilege=PrivilegeCodes.OWNER)


class GroupAccess(models.Model):
    """ GroupAccess is in essence a group profile object
    """

    ####################################
    # Members are actually recorded in a separate model.
    # Membership is equivalent with holding some privilege over the group.
    # There is a well-defined notion of PrivilegeCodes.NONE for group,
    # which to be a member with no privileges over the group, including
    # even being able to view the member list. However, this is currently disallowed
    ####################################

    # Django Group object: this has a side effect of creating Group.gaccess back relation.
    group = models.OneToOneField(Group, 
				 editable=False, 
				 null=False,
                                 related_name='gaccess',
                                 related_query_name='gaccess',
                                 help_text='group object that this object protects')

    # # syntactic sugar: make some queries easier to write
    # # ELIMINATED 1/13/2016 to avoid problematic query behavior
    # members = models.ManyToManyField(User, editable=False,
    #                                  through=UserGroupPrivilege,
    #                                  through_fields=('group', 'user'),
    #                                  related_name='user2group',  # not used, but django requires it
    #                                  help_text='members of the group')
    # held_resources = models.ManyToManyField(BaseResource, editable=False,
    #                                         through=GroupResourcePrivilege,
    #                                         through_fields=('group', 'resource'),
    #                                         related_name='resource2group',  # not used, but django requires it
    #                                         help_text='resources held by the group')

    # these are common to groups and resources and mean the same things

    # DEPRECATED: eliminate all functional references. 
    active = models.BooleanField(default=True, 
				 editable=False,
                                 help_text='whether group is currently active')

    discoverable = models.BooleanField(default=True, 
				       editable=False,
                                       help_text='whether group description is discoverable by everyone')

    public = models.BooleanField(default=True, 
				 editable=False,
                                 help_text='whether group members can be listed by everyone')

    shareable = models.BooleanField(default=True, 
				    editable=False,
                                    help_text='whether group can be shared by non-owners')

    @property
    def members(self):
        """ Replacement for many-to-many relationship

        :return: QuerySet of users

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
        return User.objects.filter(is_active=True, 
				   u2ugp__group=self.group)

    @property
    def held_resources(self):
        """ Replacement for many-to-many relationship

        :return: QuerySet of resources

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
        return BaseResource.objects.filter(r2grp__group=self.group)

    ####################################
    # compute statistics to enable "number-of-owners" logic
    ####################################

    def get_members(self):
        """ DEPRECATED: Get members of a group: use self.members instead

        :return: List of user objects who are members
        """
        return self.members

    def get_held_resources(self):
        """ DEPRECATED: Get resources held by group. use held_resources

        :return: List of resource objects held by group.
        """
        return self.held_resources

    def get_number_of_held_resources(self):
        """ DEPRECATED: Get number of resources held by group. Use members.count()

        :return: Integer number of resources held by group.
        """
        return self.held_resources.count()

    def get_editable_resources(self):
        """
        Get a list of resources that can be edited by group.

        :return: List of resource objects that can be edited  by this group.
        """
        return BaseResource.objects.filter(r2grp__group=self.group, raccess__immutable=False,
                                              r2grp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    def get_owners(self):
        """
        Return list of owners for a group.

        :return: list of users

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(is_active=True,
				   u2ugp__group=self.group,
                                   u2ugp__privilege=PrivilegeCodes.OWNER).distinct()

    def get_number_of_owners(self):
        """
        DEPRECATED: Return number of owners for a group.

        :return: Integer

        This eliminates duplicates due to multiple invitations.
        """
        return self.get_owners().count()

    def get_number_of_owner_records(self):
        """
        DEPRECATED: Return number of owner records for a group

        :return: QuerySet that evaluates to an integer number of owner records

        This can be *greater* than the number of owners due to duplicate owner 
        invitations from different users. However, this will not be true in the next release. 
        """
        return UserGroupPrivilege.objects.filter(group=self.group, privilege=PrivilegeCodes.OWNER).count()

    def get_number_of_members(self):
        """
        Return number of members of current group

        :return: QuerySet that evaluates ot an integer number of members

        This eliminates duplicates due to multiple invitations.
        """
        # Multiple invitations can create duplicates in provenance table.
        return self.get_members().count()

    def get_user_privilege(self, this_user):
        """
        Return cumulative privilege for a user over a group

        :param this_user: User to check
        :return: Privilege code 1-4
        """
        p = UserGroupPrivilege.objects.filter(group=self.group,
                                              user=this_user,
                                              user__uaccess__is_active=True)\
            .aggregate(models.Min('privilege'))
        val = p['privilege__min']
        if val is None:
            val = PrivilegeCodes.NONE
        return val


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

    # # syntactic sugar: make some queries easier to write
    # # ELIMINATED 1/13/2016 to avoid problematic query behavior
    # holding_users = models.ManyToManyField(User,
    #                                        editable=False,
    #                                        through=UserResourcePrivilege,
    #                                        through_fields=('resource', 'user'),
    #                                        related_name='user2resource',  # not used, but django requires it
    #                                        help_text='users who hold this resource')
    #
    # holding_groups = models.ManyToManyField(Group,
    #                                         editable=False,
    #                                         through=GroupResourcePrivilege,
    #                                         through_fields=('resource', 'group'),
    #                                         related_name='group2resource',  # not used, but django requires it
    #                                         help_text='groups that hold this resource')

    # these apply to both resources and groups
    active = models.BooleanField(default=True, help_text='whether resource is currently active')
    discoverable = models.BooleanField(default=False, help_text='whether resource is discoverable by everyone')
    public = models.BooleanField(default=False, help_text='whether resource data can be viewed by everyone')
    shareable = models.BooleanField(default=True, help_text='whether resource can be shared by non-owners')

    # these are for resources only
    published = models.BooleanField(default=False, help_text='whether resource has been published')
    immutable = models.BooleanField(default=False, help_text='whether to prevent all changes to the resource')

    @property
    def holding_groups(self):
        """ Replacement for many-to-many relationship

        :return: QuerySet of groups

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
        return Group.objects.filter(g2grp__resource=self.resource)

    @property
    def holding_users(self):
        """ Replacement for many-to-many relationship

        :return: QuerySet of groups

	This replaces a fairly problematic many-to-many relationship and is a property 
        so that it is a workalike for that relationship. 
        """
        return User.objects.filter(is_active=True, 
				   u2urp__resource=self.resource)

    #############################################
    # workalike queries adapt to old access control system
    #############################################

    @property
    def view_users(self):
	""" 
	QuerySet of users with view privileges
        
	This is a property so that it is a workalike for a prior explicit list 
        """
        return User.objects.filter(is_active=True, 
				   u2urp__resource=self.resource,
                                   u2urp__privilege__lte=PrivilegeCodes.VIEW)

    @property
    def edit_users(self):
	""" 
	QuerySet of users with change privileges
        
	This is a property so that it is a workalike for a prior explicit list 
        """
        return User.objects.filter(is_active=True, 
				   u2urp__resource=self.resource,
                                   u2urp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def view_groups(self):
	""" 
	QuerySet of groups with view privileges
        
	This is a property so that it is a workalike for a prior explicit list 
        """
        return Group.objects.filter(g2grp__resource=self.resource,
                                    g2grp__privilege__lte=PrivilegeCodes.VIEW)

    @property
    def edit_groups(self):
	""" 
	QuerySet of groups with edit privileges
        
	This is a property so that it is a workalike for a prior explicit list 
        """
	return Group.objects.filter(g2grp__resource=self.resource,
				    g2grp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def owners(self):
	""" 
	QuerySet of users with owner privileges
        
	This is a property so that it is a workalike for a prior explicit list 
        """
        return self.get_owners()

    #############################################
    # Reporting of resource statistics
    # including counts of users who own a resource
    #############################################
    def get_owners(self):
        """
        Get a list of owner objects for the current resource

        :return: QuerySet that evaluates to a list of user objects
        """
        return User.objects.filter(is_active=True, 
				   u2urp__privilege=PrivilegeCodes.OWNER,
                                   u2urp__resource=self.resource)

    def get_number_of_owners(self):
        """
        DEPRECATED: Call count() explicitly. Get number of owners for the current resource.

        :return: Integer number of owners
        """

        return self.get_owners().count()

    def get_number_of_owner_records(self):
        """
        DEPRECATED: Return number of owner records for a group

        :return: Integer number of owner records

        This can be *greater* than the number of owners due to duplicate owner
        invitations from different users. However, this condition is itself DEPRECATED
        and will become impossible in the next release. 
        """
        return UserResourcePrivilege.objects.filter(resource=self.resource,
                                                    privilege=PrivilegeCodes.OWNER).count()

    def get_users(self):
        """
        DEPRECATED: use holding_users instead. Return a list of all users with access to resource.

        :return: QuerySet that evaluates to all users holding resource.
        """
        return self.holding_users

    def get_number_of_users(self):
        """
        DEPRECATED: Number of users with explicit access to resource, excluding group access.

        :return: Integer number of users with access to resource

        This excludes group access and only counts individual access.

	DEPRECATED: use explicit count() instead. 
        """
        return self.holding_users.count()


    def get_groups(self):
        """
        DEPRECATED: Get a list of group objects with permission over the resource.

        :return: List of group objects.

	DEPRECATED: use holding_groups instead. 
        """
        return self.holding_groups

    def get_number_of_groups(self):
        """
        DEPRECATED Number of groups with access to a resource

        :return: Integer number of groups that can access resource

        This excludes individual access by users

	DEPRECATED: use explicit count() instead 
        """
        return self.holding_groups.count()

    def get_holders(self):
        """
        Return a list of all users who hold some privilege over the resource self, either individual or group.

        :return: List of User objects.
        """
        # The query here is quite subtle.
        # We want user objects that either
        # a) have direct access to the resource or
        # b) have access to a group that has access to a resource
        return User.objects.filter(Q(is_active=True)
                                 & (Q(u2urp__resource=self.resource)
                                  | Q(u2ugp__group__g2grp__resource=self.resource)))

    def get_number_of_holders(self):
        """
        DEPRECATED: use explicit count() instead. Return number of users with any kind of privilege over this resource

        :return: an Integer

        This includes users with direct privilege and users with group privilege, and eliminates duplicates.
        """
        # OLD:  return self.get_holders().count()
        return self.get_holders().count()

    def get_combined_privilege(self, this_user):
        """
        Return the privilege of a specific user over this resource

        :param this_user: the user upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This reports combined privilege of a user due to user permissions and group permissions, but does
        not account for resource flags.

        Note that this privilege is the privilege that the user holds, not the privilege
        in effect due to flags.  See "get_effective_privilege" to account for flags.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        if this_user.is_superuser:
            return PrivilegeCodes.OWNER

        # compute simple user privilege over resource
        user_priv = UserResourcePrivilege.objects\
            .filter(user=this_user,
                    user__is_active=True,
                    resource=self.resource)\
            .aggregate(models.Min('privilege'))

        # this realizes the query early, but can't be helped, because otherwise,
        # I would be stuck with a possibility of a None return from the two unrealized queries.
        response1 = user_priv['privilege__min']
        if response1 is None:
            response1 = PrivilegeCodes.NONE

        # include group active flag
        group_priv = GroupResourcePrivilege.objects\
            .filter(resource=self.resource,
                    group__g2ugp__user=this_user,
                    group__g2ugp__user__is_active=True)\
            .aggregate(models.Min('privilege'))

        # this realizes the query early, but can't be helped, because otherwise,
        # I would be stuck with a possibility of a None return from the two unrealized queries.
        response2 = group_priv['privilege__min']
        if response2 is None:
            response2 = PrivilegeCodes.NONE

        return min(response1, response2)

    def get_group_privilege(self, this_group):
        """
        Return the privilege of a specific group over this resource

        :param this_group: the group upon which to report
        :return: integer privilege 1-4 (PrivilegeCodes)

        This reports the privilege arising from group membership only.

        Note that this privilege is the privilege that the group holds, and not the privilege in effect
        due to resource flags.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_group, Group)

        # compute simple user privilege over resource
        response1 = GroupResourcePrivilege.objects.filter(group=this_group,
                                                          resource=self.resource)\
            .aggregate(models.Min('privilege'))['privilege__min']

        if response1 is None:
            response1 = PrivilegeCodes.NONE

        return response1

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
        user_priv = self.get_combined_privilege(this_user)
        if self.immutable:
            user_priv = max(user_priv, PrivilegeCodes.VIEW)
        if self.public:
            user_priv = min(user_priv, PrivilegeCodes.VIEW)
        return user_priv
