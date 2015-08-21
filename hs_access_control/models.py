__author__ = 'Alva'

from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.conf import settings

from hs_core.models import GenericResource


######################################
######################################
# Access control subsystem
######################################
######################################

# TODO: invite/accept/refuse logic (including invitation classes)
# TODO: basic polymorphic routines user.can_change, user.can_view
# TODO: ensure that user and group active flags work properly in access control queries.
# TODO: there is a small chance of a race condition that could result in removal of the last resource or group owner.

# NOTES and quandaries

# 1) There is a basic problem of semantics in sharing.
#    We need to know whether to put a "share" button on the screen.
#    But this button can't share with just anyone, e.g., self.
#    However, the permissions system is somewhat blind to this.
#    Thus, we have some problems with "too much specificity" versus "too little".
# PROPOSED SOLUTION:
#    One can share with self but can only downgrade privilege.
#    Thus, the user list becomes unrestricted.

# 2) The options for unshare_*_with_* are too confusing. It tries to do
#    two different kinds of things:
#   a) completely remove a share (an owner privilege)
#   b) undo a prior share (an unprivileged action).
# PROPOSED SOLUTION:
#   a) split "undo" function out of unshare_*_with_* and into
#      undo_share_*_with_*. This eliminates the potential confusion.
#   b) unshare_* undoes the whole share; undo_share_* undoes one sharing
#      action.


######################################
# Exceptions specific to access control:
# a) Access Exception: permission denied
# b) Usage Exception: bad parameters
# c) Integrity Exception: database corrupt
######################################
class HSAException(Exception):
    """
    Generic Base Exception class for HSAccess class.

    *This exception is a generic base class and is never directly raised.*
    See subclasses HSAccessException, HSUsageException, and HSIntegrityException
    for details.
    """


class HSAccessException(HSAException):
    """
    Exception class for access control.

    This exception is raised when the access control system denies a user request.
    It can safely be caught to probe whether an operation is permitted.
    """
    def __str__(self):
        return repr("HS Access Exception: " + self.message)

    pass


class HSAUsageException(HSAException):
    """
    Exception class for parameter usage problems.

    This exception is raised when a routine is called with invalid parameters.
    This includes references to non-existent resources, groups, and users.

    This is typically a programming error and should be entered into
    issue tracker and resolved.

    *Catching this exception is not recommended.*
    """
    def __str__(self):
        return repr("HS Usage Exception: " + self.message)

    pass


# in this implementation, integrity exceptions are extremely unlikely.
class HSAIntegrityException(HSAException):
    """
    Exception class for database failures.
    This is an "anti-bugging" exception that should *never* be raised unless something
    is very seriously wrong with database configuration. This exception is only raised
    if the database fails to meet integrity constraints.

    *This cannot be a programming error.* In fact, it can only happen if the schema
    for the database itself becomes corrupt. The only way to address this is to
    repair the schema.

    *Catching this exception is not recommended.*
    """

    def __str__(self):
        return repr("HS Database Integrity Exception: " + self.message)

    pass

####################################
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
####################################


####################################
# privileges are numeric codes 1-4
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


####################################
# command codes for multimodal routines
####################################
class CommandCodes(object):
    """
    Command codes describe nature of a request.
    """
    CHECK = 1
    DO = 2


####################################
# user membership in groups
####################################

class UserGroupPrivilege(models.Model):
    """ Privileges of a user over a group

    Having any privilege over a group is synonymous with membership.

    There is a reasonable meaning to PrivilegeCodes.NONE, which is to be
    a group member without the ability to discover the identities of other group members.
    However, this is currently disallowed.
    """

    privilege = models.IntegerField(choices=PrivilegeCodes.PRIVILEGE_CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    start = models.DateTimeField(editable=False, auto_now=True)

    # I don't like to allow nulls, but the alternative is to supply
    # a bogus default, which would be transparently applied during
    # migrations and is a worse option.

    user = models.ForeignKey('UserAccess', null=True, editable=False, related_name='u2ugp',
                             help_text='user to be granted privilege')
    group = models.ForeignKey('GroupAccess', null=True, editable=False, related_name='g2ugp',
                              help_text='group to which privilege applies')
    grantor = models.ForeignKey('UserAccess', null=True, editable=False, related_name='x2ugp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = (('user', 'group', 'grantor'),)


####################################
# user access to resources
####################################

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

    # I don't like to allow nulls, but the alternative is to supply
    # a bogus default, which would be transparently applied during
    # migrations and is a worse option.

    user = models.ForeignKey('UserAccess', null=True, editable=False,
                             related_name='u2urp',
                             help_text='user to be granted privilege')
    resource = models.ForeignKey('ResourceAccess', null=True, editable=False,
                                 related_name="r2urp",
                                 help_text='resource to which privilege applies')
    grantor = models.ForeignKey('UserAccess', null=True, editable=False,
                                related_name='x2urp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = (('user', 'resource', 'grantor'),)


####################################
# group access to resources
####################################

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

    # I don't like to allow nulls, but the alternative is to supply
    # a bogus default, which would be transparently applied during
    # migrations and is a worse option.

    group = models.ForeignKey('GroupAccess', null=True, editable=False,
                              related_name='g2grp',
                              help_text='group to be granted privilege')
    resource = models.ForeignKey('ResourceAccess', null=True, editable=False,
                                 related_name='r2grp',
                                 help_text='resource to which privilege applies')
    grantor = models.ForeignKey('UserAccess', null=True, editable=False,
                                related_name='x2grp',
                                help_text='grantor of privilege')

    class Meta:
        unique_together = (('group', 'resource', 'grantor'),)


######################################
# UserAccess class references User class similar to a User profile
######################################
class UserAccess(models.Model):

    """
    UserAccess is in essence a user profile object.
    We relate it to the native User model via the following cryptic code.
    This ensures that if we ever change our user model, this will adapt.
    This creates a back-relation User.uaccess to access this model.

    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, editable=False, null=True,
                                related_name='uaccess',
                                related_query_name='uaccess')

    active = models.BooleanField(default=True, editable=False, help_text='whether user is currently capable of action')
    admin = models.BooleanField(default=False, editable=False, help_text='whether user is an administrator')

    # syntactic sugar: make some queries easier to write
    # related names are not used by our application, but trying to
    # turn them off breaks queries to these objects.
    held_resources = models.ManyToManyField('ResourceAccess',
                                            editable=False,
                                            through='UserResourcePrivilege',
                                            through_fields=('user', 'resource'),
                                            related_name='resource2user',  # not used, but django requires it
                                            help_text='resources held by this user')
    held_groups = models.ManyToManyField('GroupAccess',
                                         editable=False,
                                         through='UserGroupPrivilege',
                                         through_fields=('user', 'group'),
                                         related_name='group2user',  # not used, but django requires it
                                         help_text='groups held by this user')

    @staticmethod
    def __helper():
        from .utils import AccessControlHelper
        return AccessControlHelper

    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: groups
    ##########################################
    ##########################################

    def create_group(self, title):
        return UserAccess.__helper().create_group(self, title)

    def delete_group(self, this_group):
        UserAccess.__helper().delete_group(self, this_group)

    ################################
    # public and discoverable groups
    ################################

    @staticmethod
    def get_discoverable_groups():
        return UserAccess.__helper().get_discoverable_groups()

    @staticmethod
    def get_public_groups():
        return UserAccess.__helper().get_public_groups()

    ################################
    # held and owned group
    ################################

    def get_held_groups(self):
        return UserAccess.__helper().get_held_groups(self)

    def get_number_of_held_groups(self):
        return UserAccess.__helper().get_number_of_held_groups(self)

    def get_owned_groups(self):
        return UserAccess.__helper().get_owned_groups(self)

    def get_number_of_owned_groups(self):
        """
        Get number of groups owned by current user

        :return: Integer

        This is a separate procedure, rather than being implemented as get_owned_groups().count(),
        due to performance concerns.
        """
        return self.get_owned_groups().count()

    #################################
    # access checks for groups
    #################################

    def owns_group(self, this_group):
        return UserAccess.__helper().owns_group(self, this_group)

    def can_change_group(self, this_group):
        return UserAccess.__helper().can_change_group(self, this_group)

    def can_view_group(self, this_group):
        return UserAccess.__helper().can_view_group(self, this_group)

    def can_view_group_metadata(self, this_group):
        return UserAccess.__helper().can_view_group_metadata(self, this_group)

    def can_change_group_flags(self, this_group):
        return UserAccess.__helper().can_change_group_flags(self, this_group)

    def can_delete_group(self, this_group):
        return UserAccess.__helper().can_delete_group(self, this_group)

    ####################################
    # sharing permission checking
    ####################################

    def can_share_group(self, this_group, this_privilege):
        return UserAccess.__helper().can_share_group(self, this_group, this_privilege)

    ####################################
    # group membership sharing
    ####################################

    def share_group_with_user(self, this_group, this_user, this_privilege):
        UserAccess.__helper().share_group_with_user(self, this_group, this_user, this_privilege)

    def unshare_group_with_user(self, this_group, this_user):
        return UserAccess.__helper().unshare_group_with_user(self, this_group, this_user)

    def can_unshare_group_with_user(self, this_group, this_user):
        return UserAccess.__helper().can_unshare_group_with_user(self, this_group, this_user)

    def undo_share_group_with_user(self, this_group, this_user, this_grantor=None):
        return UserAccess.__helper().undo_share_group_with_user(self, this_group, this_user, this_grantor)

    def can_undo_share_group_with_user(self, this_group, this_user, this_grantor=None):
        return UserAccess.__helper().can_undo_share_group_with_user(self, this_group, this_user, this_grantor)

    ##########################################
    # users whose access could be undone by self
    ##########################################
    def get_group_undo_users(self, this_group):
        return UserAccess.__helper().get_group_undo_users(self, this_group)

    def get_group_unshare_users(self, this_group):
        return UserAccess.__helper().get_group_unshare_users(self, this_group)

    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: resources
    ##########################################
    ##########################################

    ##########################################
    # held and owned resources
    ##########################################

    def get_held_resources(self):
        return UserAccess.__helper().get_held_resources(self)

    def get_number_of_held_resources(self):
        return UserAccess.__helper().get_number_of_held_resources(self)

    def get_owned_resources(self):
        return UserAccess.__helper().get_owned_resources(self)

    def get_number_of_owned_resources(self):
        return UserAccess.__helper().get_number_of_owned_resources(self)

    def get_editable_resources(self):
        return UserAccess.__helper().get_editable_resources(self)

    #############################################
    # Check access permissions for self (user)
    #############################################

    def owns_resource(self, this_resource):
        return UserAccess.__helper().owns_resource(self, this_resource)

    def can_change_resource(self, this_resource):
        return UserAccess.__helper().can_change_resource(self, this_resource)

    def can_change_resource_flags(self, this_resource):
        return UserAccess.__helper().can_change_resource_flags(self, this_resource)

    def can_view_resource(self, this_resource):
        return UserAccess.__helper().can_view_resource(self, this_resource)

    def can_delete_resource(self, this_resource):
        return UserAccess.__helper().can_delete_resource(self, this_resource)

    ##########################################
    # check sharing rights
    ##########################################

    def can_share_resource(self, this_resource, this_privilege):
        return UserAccess.__helper().can_share_resource(self, this_resource, this_privilege)

    def can_share_resource_with_group(self, this_resource, this_group, this_privilege):
        return UserAccess.__helper().can_share_resource_with_group(self, this_resource, this_group, this_privilege)

    def undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        return UserAccess.__helper().undo_share_resource_with_group(self, this_resource, this_group, this_grantor)

    def can_undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        return UserAccess.__helper().can_undo_share_resource_with_group(self, this_resource, this_group, this_grantor)

    #################################
    # share and unshare resources with user
    #################################
    def share_resource_with_user(self, this_resource, this_user, this_privilege):
        UserAccess.__helper().share_resource_with_user(self, this_resource, this_user, this_privilege)

    def unshare_resource_with_user(self, this_resource, this_user):
        return UserAccess.__helper().unshare_resource_with_user(self, this_resource, this_user)

    def can_unshare_resource_with_user(self, this_resource, this_user):
        return UserAccess.__helper().can_unshare_resource_with_user(self, this_resource, this_user)

    def undo_share_resource_with_user(self, this_resource, this_user, this_grantor=None):
        return UserAccess.__helper().undo_share_resource_with_user(self, this_resource, this_user, this_grantor)

    def can_undo_share_resource_with_user(self, this_resource, this_user, this_grantor=None):
        return UserAccess.__helper().can_undo_share_resource_with_user(self, this_resource, this_user, this_grantor)

    ######################################
    # share and unshare resource with group
    ######################################
    def share_resource_with_group(self, this_resource, this_group, this_privilege):
        UserAccess.__helper().share_resource_with_group(self, this_resource, this_group, this_privilege)

    def unshare_resource_with_group(self, this_resource, this_group):
        return UserAccess.__helper().unshare_resource_with_group(self, this_resource, this_group)

    def can_unshare_resource_with_group(self, this_resource, this_group):
        return UserAccess.__helper().can_unshare_resource_with_group(self, this_resource, this_group)

    ##########################################
    # users whose access could be undone by self
    ##########################################
    def get_resource_undo_users(self, this_resource):
        return UserAccess.__helper().get_resource_undo_users(self, this_resource)

    def get_resource_unshare_users(self, this_resource):
        return UserAccess.__helper().get_resource_unshare_users(self, this_resource)

    def get_resource_undo_groups(self, this_resource):
        return UserAccess.__helper().get_resource_undo_groups(self, this_resource)

    def get_resource_unshare_groups(self, this_resource):
        return UserAccess.__helper().get_resource_unshare_groups(self, this_resource)


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
    group = models.OneToOneField(Group, editable=False, null=True,
                                 related_name='gaccess',
                                 related_query_name='gaccess',
                                 help_text='group object that this object protects')

    # syntactic sugar: make some queries easier to write
    # related names are not used by our application, but trying to
    # turn them off breaks queries to these objects.
    members = models.ManyToManyField('UserAccess', editable=False,
                                     through=UserGroupPrivilege,
                                     through_fields=('group', 'user'),
                                     related_name='user2group',  # not used, but django requires it
                                     help_text='members of the group')
    held_resources = models.ManyToManyField('ResourceAccess', editable=False,
                                            through=GroupResourcePrivilege,
                                            through_fields=('group', 'resource'),
                                            related_name='resource2group',  # not used, but django requires it
                                            help_text='resources held by the group')

    # these are common to groups and resources and mean the same things
    active = models.BooleanField(default=True, editable=False,
                                 help_text='whether group is currently active')
    discoverable = models.BooleanField(default=True, editable=False,
                                       help_text='whether group description is discoverable by everyone')
    public = models.BooleanField(default=True, editable=False,
                                 help_text='whether group members can be listed by everyone')
    shareable = models.BooleanField(default=True, editable=False,
                                    help_text='whether group can be shared by non-owners')


    ####################################
    # compute statistics to enable "number-of-owners" logic
    ####################################

    def get_members(self):
        """
        Get members of a group

        :return: List of user objects who are members
        """
        return User.objects.filter(uaccess__held_groups=self).distinct()

    def get_held_resources(self):
        """
        Get resources held by group.

        :return: List of resource objects held by group.
        """
        return GenericResource.objects.filter(raccess__holding_groups=self)

    def get_number_of_held_resources(self):
        """
        Get number of resources held by group.

        :return: Integer number of resources held by group.
        """

        return self.held_resources.distinct().count()

    def get_editable_resources(self):
        """
        Get a list of resources that can be edited by group.

        :return: List of resource objects that can be edited  by this group.
        """
        return GenericResource.objects.filter(raccess__r2grp__user=self, raccess__immutable=False,
                                              raccess__r2grp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    def get_owners(self):
        """
        Return list of owners for a group.

        :return: list

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(uaccess__u2ugp__group=self,
                                   uaccess__u2ugp__privilege=PrivilegeCodes.OWNER).distinct()

    def get_number_of_owners(self):
        """
        Return number of owners for a group.

        :return: Integer

        This eliminates duplicates due to multiple invitations.
        """
        return self.get_owners().count()

    def get_number_of_owner_records(self):
        """
        Return number of owner records for a group
        :return: QuerySet that evaluates to an integer number of owner records

        This can be *greater* than the number of owners due to duplicate owner invitations from different users.
        """
        return UserGroupPrivilege.objects.filter(group=self, privilege=PrivilegeCodes.OWNER).count()

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
        Return cumulative privilege for a user

        :param this_user: User to check
        :return: Privilege code 1-4
        """
        p = UserGroupPrivilege.objects.filter(group=self,
                                              user=this_user,
                                              user__active=True)\
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

    resource = models.OneToOneField(GenericResource,
                                    editable=False,
                                    null=True,
                                    related_name='raccess',
                                    related_query_name='raccess')
    # syntactic sugar: make some queries easier to write
    # related names are not used by our application, but trying to
    # turn them off breaks queries to these objects.
    holding_users = models.ManyToManyField('UserAccess',
                                           editable=False,
                                           through=UserResourcePrivilege,
                                           through_fields=('resource', 'user'),
                                           related_name='user2resource',  # not used, but django requires it
                                           help_text='users who hold this resource')
    holding_groups = models.ManyToManyField('GroupAccess',
                                            editable=False,
                                            through=GroupResourcePrivilege,
                                            through_fields=('resource', 'group'),
                                            related_name='group2resource',  # not used, but django requires it
                                            help_text='groups that hold this resource')

    # these apply to both resources and groups
    active = models.BooleanField(default=True, help_text='whether resource is currently active')
    discoverable = models.BooleanField(default=False, help_text='whether resource is discoverable by everyone')
    public = models.BooleanField(default=False, help_text='whether resource data can be viewed by everyone')
    shareable = models.BooleanField(default=True, help_text='whether resource can be shared by non-owners')
    # these are for resources only
    published = models.BooleanField(default=False, help_text='whether resource has been published')
    immutable = models.BooleanField(default=False, help_text='whether to prevent all changes to the resource')

    #############################################
    # workalike queries adapt to old access control system
    #############################################

    @property
    def view_users(self):
        return User.objects.filter(uaccess__u2urp__resource=self,
                                   uaccess__u2urp__privilege__lte=PrivilegeCodes.VIEW).distinct()

    @property
    def edit_users(self):
        return User.objects.filter(uaccess__u2urp__resource=self,
                                   uaccess__u2urp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    @property
    def view_groups(self):
        return Group.objects.filter(gaccess__g2grp__resource=self,
                                    gaccess__g2grp__privilege__lte=PrivilegeCodes.VIEW).distinct()

    @property
    def edit_groups(self):
        return Group.objects.filter(gaccess__g2grp__resource=self,
                                    gaccess__g2grp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    @property
    def owners(self):
        return User.objects.filter(uaccess__u2urp__privilege=PrivilegeCodes.OWNER,
                                   uaccess__u2urp__resource=self)

    #############################################
    # Reporting of resource statistics
    # including counts of users who own a resource
    #############################################
    def get_owners(self):
        """
        Get a list of owner objects for the current resource
        """

        return User.objects.filter(uaccess__u2urp__privilege=PrivilegeCodes.OWNER,
                                   uaccess__u2urp__resource=self)

    def get_number_of_owners(self):
        """
        Get number of owners for the current resource.

        :return: Integer number of owners

        This must eliminate duplicates due to the possibility of
        multiple owner records for the same resource and user.
        """

        return self.get_owners().count()

    def get_number_of_owner_records(self):
        """
        Return number of owner records for a group

        :return: Integer number of owner records

        This can be *greater* than the number of owners due to duplicate owner
        invitations from different users.
        """
        return UserResourcePrivilege.objects.filter(resource=self,
                                                    privilege=PrivilegeCodes.OWNER).count()

    def get_users(self):
        """
        Return a list of all users with access to resource.

        :return: QuerySet that evaluates to all users holding resource.
        """
        return User.objects.filter(uaccess__held_resources=self)

    def get_number_of_users(self):
        """
        Number of users with explicit access to resource, excluding group access.

        :return: Integer number of users with access to resource

        This excludes group access and only counts individual access.
        """
        return self.get_users().count()

    def get_groups(self):
        """
        Get a list of group objects with permission over the resource.

        :return: List of group objects.
        """
        return self.holding_groups.distinct()

    def get_number_of_groups(self):
        """
        Number of groups with access to a resource

        :return: Integer number of groups that can access resource

        This excludes individual access by users
        """
        return self.get_groups().count()

    def get_holders(self):
        """
        Return a list of all users who hold some privilege over the resource self, either individual or group.

        :return: List of User objects.
        """
        # The query here is quite subtle.
        # We want user objects that either
        # a) have direct access to the resource or
        # b) have access to a group that has access to a resource
        return User.objects.filter(Q(uaccess__held_resources=self)
                                 | Q(uaccess__held_groups__held_resources=self)).distinct()

    def get_number_of_holders(self):
        """
        Return number of users with any kind of privilege over this resource
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

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        # compute simple user privilege over resource
        user_priv = UserResourcePrivilege.objects\
            .filter(user=access_user,
                    user__active=True,
                    resource=self)\
            .aggregate(models.Min('privilege'))

        # this realizes the query early, but can't be helped, because otherwise,
        # I would be stuck with a possibility of a None return from the two unrealized queries.
        response1 = user_priv['privilege__min']
        if response1 is None:
            response1 = PrivilegeCodes.NONE

        group_priv = GroupResourcePrivilege.objects\
            .filter(resource=self,
                    group__active=True,
                    group__members=access_user)\
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
        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        # compute simple user privilege over resource
        response1 = GroupResourcePrivilege.objects.filter(group=access_group,
                                                          group__active=True,
                                                          resource=self)\
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
