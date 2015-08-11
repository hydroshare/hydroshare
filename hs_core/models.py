from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.contrib.auth import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django import forms
from django.utils.timezone import now
from mezzanine.pages.models import Page, RichText
from mezzanine.pages.page_processors import processor_for
from uuid import uuid4
from mezzanine.core.models import Ownable
from mezzanine.generic.fields import CommentsField, RatingField
from mezzanine.conf import settings as s
from mezzanine.generic.models import Keyword, AssignedKeyword
import os.path
from django_irods.storage import IrodsStorage
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from languages_iso import languages as iso_languages
from dateutil import parser
import json

class GroupOwnership(models.Model):
    group = models.ForeignKey(Group)
    owner = models.ForeignKey(User)


def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    NOTE: The API key portion has been removed with TastyPie and will be restored when the
    new API is built.

    :param request:
    :return: django.contrib.auth.User
    """

    if request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user


def validate_user_url(value):
    err_message = '%s is not a valid url for hydroshare user' % value
    if value:
        url_parts = value.split('/')
        if len(url_parts) != 6:
            raise ValidationError(err_message)
        if url_parts[3] != 'user':
            raise ValidationError(err_message)

        try:
            user_id = int(url_parts[4])
        except ValueError:
            raise ValidationError(err_message)

        # check the user exists for the provided user id
        if not User.objects.filter(pk=user_id).exists():
            raise ValidationError(err_message)


class ResourcePermissionsMixin(Ownable):
    creator = models.ForeignKey(User,
                                related_name='creator_of_%(app_label)s_%(class)s',
                                help_text='This is the person who first uploaded the resource',
                                )

    public = models.BooleanField(
        help_text='If this is true, the resource is viewable and downloadable by anyone',
        default=True
    )

    owners = models.ManyToManyField(User,
                                    related_name='owns_%(app_label)s_%(class)s',
                                    help_text='The person who has total ownership of the resource'
    )
    frozen = models.BooleanField(
        help_text='If this is true, the resource should not be modified',
        default=False
    )
    do_not_distribute = models.BooleanField(
        help_text='If this is true, the resource owner has to designate viewers',
        default=False
    )
    discoverable = models.BooleanField(
        help_text='If this is true, it will turn up in searches.',
        default=True
    )
    published_and_frozen = models.BooleanField(
        help_text="Once this is true, no changes can be made to the resource",
        default=False
    )

    view_users = models.ManyToManyField(User,
                                        related_name='user_viewable_%(app_label)s_%(class)s',
                                        help_text='This is the set of Hydroshare Users who can view the resource',
                                        null=True, blank=True)

    view_groups = models.ManyToManyField(Group,
                                         related_name='group_viewable_%(app_label)s_%(class)s',
                                         help_text='This is the set of Hydroshare Groups who can view the resource',
                                         null=True, blank=True)

    edit_users = models.ManyToManyField(User,
                                        related_name='user_editable_%(app_label)s_%(class)s',
                                        help_text='This is the set of Hydroshare Users who can edit the resource',
                                        null=True, blank=True)

    edit_groups = models.ManyToManyField(Group,
                                         related_name='group_editable_%(app_label)s_%(class)s',
                                         help_text='This is the set of Hydroshare Groups who can edit the resource',
                                         null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def permissions_store(self):
        return s.PERMISSIONS_DB

    def can_add(self, request):
        return self.can_change(request)

    def can_delete(self, request):
        user = get_user(request)
        if user.is_authenticated():
            if user.is_superuser or self.raccess.owners.filter(pk=user.pk).exists():
                return True
            else:
                return False
        else:
            return False

    def can_change(self, request):
        user = get_user(request)

        if user.is_authenticated():
            if user.is_superuser:
                return True
            elif self.raccess.owners.filter(pk=user.pk).exists():
                return True
            elif self.raccess.edit_users.filter(pk=user.pk).exists():
                return True
            elif self.raccess.edit_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            else:
                return False
        else:
            return False

    def can_view(self, request):
        user = get_user(request)

        if self.raccess.public:
            return True
        if user.is_authenticated():
            if user.is_superuser:
                return True
            elif self.raccess.owners.filter(pk=user.pk).exists():
                return True
            elif self.raccess.edit_users.filter(pk=user.pk).exists():
                return True
            elif self.raccess.view_users.filter(pk=user.pk).exists():
                return True
            elif self.raccess.edit_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            elif self.raccess.view_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            else:
                return False
        else:
            return False

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
    def __init__(self, value):
        """
        Sets the exception value to a given string.
        """
        self.value = value

    def __str__(self):
        return repr(self.value)


class HSAccessException(HSAException):
    """
    Exception class for access control.

    This exception is raised when the access control system denies a user request.
    It can safely be caught to probe whether an operation is permitted.
    """
    def __str__(self):
        return repr("HS Access Exception: " + self.value)

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
        return repr("HS Usage Exception: " + self.value)

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
        return repr("HS Database Integrity Exception: " + self.value)

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
    """
    OWNER  = 1
    CHANGE = 2
    VIEW   = 3
    NONE   = 4
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
    DO    = 2

####################################
# user membership in groups
####################################

class UserGroupPrivilege(models.Model):
    """ Privileges of a user over a group

    Privilege is a numeric code 1-4:

        * 1 or PrivilegeCodes.OWNER:
            the user owns the object.

        * 2 or PrivilegeCodes.CHANGE:
            the user can change the content of the object but not its state.

        * 3 or PrivilegeCodes.VIEW:
            the user can view but not change the object.

        * 4 or PrivilegeCodes.NONE:
            the user has no privilege over the object.

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

    user = models.ForeignKey('UserAccess', null=True, editable=False,
                                     related_name='u2ugp',
                                     help_text='user to be granted privilege')
    group = models.ForeignKey('GroupAccess', null=True, editable=False,
                                     related_name='g2ugp',
                                     help_text='group to which privilege applies')
    grantor = models.ForeignKey('UserAccess', null=True, editable=False,
                                     related_name='x2ugp',
                                     help_text='grantor of privilege')
    class Meta:
        unique_together = (('user', 'group', 'grantor'),)

####################################
# user access to resources
####################################

class UserResourcePrivilege(models.Model):
    """ Privileges of a user over a resource

    Privilege is a numeric code 1-4:

        * 1 or PrivilegeCodes.OWNER:
            the user owns the object.

        * 2 or PrivilegeCodes.CHANGE:
            the user can change the content of the object but not its state.

        * 3 or PrivilegeCodes.VIEW:
            the user can view but not change the object.

        * 4 or PrivilegeCodes.NONE:
            the user has no privilege over the object.

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

    Privilege is a numeric code 1-4:

        * 1 or PrivilegeCodes.OWNER:
            the user owns the object.

        * 2 or PrivilegeCodes.CHANGE:
            the user can change the content of the object but not its state.

        * 3 or PrivilegeCodes.VIEW:
            the user can view but not change the object.

        * 4 or PrivilegeCodes.NONE:
            the user has no privilege over the object.

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
    """ Mockup of User Profile object

    Avoid real Django User for testing purposes.
    """
    # filler metadata: not final
    # login = models.CharField(max_length=20, editable=False, default='none')
    # name = models.CharField(max_length=200, editable=True, default='none')
    # these are not editable because editing them with a form would bypass access control

    # UserAccess is in essence a user profile object.
    # We relate it to the native User model via the following cryptic code.
    # This ensures that if we ever change our user model, this will adapt.
    # This creates a back-relation User.uaccess to access this model.

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


    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: users
    ##########################################
    ##########################################

    @staticmethod
    def create_user(login, name, admin=False):
        """
        Create a user.

        :param login: User login name
        :param name: User full name
        :param admin: Whether user has administrative privileges
        :return: None

        This raises HSUsageException if a user login already exists.

        Note that there is no delete_user. Instead, one can make a
        user "u" inactive via

            u.active = False
            save()

        """

        if not User.objects.filter(username=login):
            # This is the recommended way to create a User in the raw auth model.
            # This is placeholder code only for testing.
            # Arguments are login, email, password
            raw_user = User.objects.create_user(login, login + '@foo.com', 'foo')
            raw_user.first_name = name
            raw_user.save()
            # There is something to be said for keeping this relationship pure
            u = UserAccess(user=raw_user, admin=admin)
            u.save()
            return raw_user
        else:
            raise HSAUsageException("Login already exists")

    @staticmethod
    def get_users():
        """
        Get a list of all users in the system.

        :return: List of user objects.
        """
        return User.objects.filter(uaccess__active=True)

    @staticmethod
    def get_user_from_login(login):
        """
        Get a user object from a login name.

        :param login: login name to translate.
        :return: user object.
        """
        return User.objects.get(uaccess__login=login)

    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: groups
    ##########################################
    ##########################################

    def create_group(self, title):
        """
        Create a group.

        :param title: Group title.
        :return: None

        Anyone can create a group. The creator is also the first owner.

        An owner can assign ownership to another user via share_group_with_user,
        but cannot remove self-ownership if that would leave the group with no
        owner.
        """
        raw_group = Group(name=title) # the single attribute of the group
        raw_group.save()
        g = GroupAccess(group=raw_group)
        g.save()
        # Must bootstrap access control system initially
        UserGroupPrivilege(group=g,
                           user=self,
                           grantor=self,
                           privilege=PrivilegeCodes.OWNER).save()
        return raw_group

    def delete_group(self, this_group):
        """
        Delete a group and all membership information.

        :param this_group: Group to delete.
        :return: None

        To delete a group a user must be owner or administrator of the group.
        Deleting a group deletes all membership and sharing information.
        There is no undo.
        """
        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if self.admin or self.owns_group(this_group):
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

    ################################
    # public and discoverable groups
    ################################

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

    ################################
    # held and owned group
    ################################

    def get_held_groups(self):
        """
        Get number of groups accessible to self.

        :return: QuerySet evaluating to held groups.

        This is really documentation of how to access held groups.

        A held group is fully accessible to the user in question, as if it were public.
        """
        return Group.objects.filter(gaccess__members=self)

    def get_number_of_held_groups(self):
        """
        Get number of groups held by self.

        :return: Integer number of held groups.
        """
        # returning indirect objects will take too long 
        return GroupAccess.objects.filter(members=self).count()

    def get_owned_groups(self):
        """
        Return a list of groups owned by self.

        :return: QuerySet of groups owned by self.

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
        # OLD:  ids = UserGroupPrivilege.objects.filter(user=self, privilege=PrivilegeCodes.OWNER) \
        # OLD:      .values_list('group_id', flat=True).distinct()
        # OLD:  return Group.objects.filter(gaccess__pk__in=ids)
        # OLD:  According to the docs, the above actually represents one nested query, not two
        return Group.objects.filter(gaccess__g2ugp__user=self,
                                    gaccess__g2ugp__privilege=PrivilegeCodes.OWNER).distinct()

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
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege=PrivilegeCodes.OWNER,
                                             user=self):
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
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        if not self.active:
            return False

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege__lte=PrivilegeCodes.CHANGE,
                                             user=self):
            return True
        else:
            return False

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
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        # allow access to public resources even if user is not logged in.
        if not self.active:
            return False
        if access_group.public:
            return True

        if UserGroupPrivilege.objects.filter(group=access_group,
                                             privilege__lte=PrivilegeCodes.VIEW,
                                             user=self):
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

        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        if not self.active:
            return False

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
        --------------

        This routine is called *both* when building views and when writing responders.
        It should be called on both sides of the connection.

            * In a view builder, it determines whether buttons are shown for flag changes.

            * In a responder, it determines whether the request is valid.

        At this point, the return value is synonymous with ownership or admin.
        This may not always be true. So it is best to explicitly call this function
        rather than assuming implications between functions.
        """
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        return self.active and (self.admin or self.owns_group(this_group))

    def can_delete_group(self, this_group):
        """
        Whether the current user can delete a group.

        :param this_group: group to query
        :return: True if the user can delete it.

        Usage:

            if my_user.can_delete_group(some_group):
                my_user.delete_group(some_group)
            else:
                raise HSAccessException("Insufficient privilege")

        In practice:
        --------------

        At this point, this is synonymous with ownership or admin. This may not always be true.
        So it is best to explicitly call this function rather than assuming implications
        between functions.
        """
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        return self.active and (self.admin or self.owns_group(this_group))

    ####################################
    # sharing permission checking
    ####################################

    def can_share_group(self, this_group, this_privilege):
        """
        Return True if a given user can share this resource with a given privilege.

        :param this_group: group to check
        :param this_privilege: privilege to assign
        :return: True if sharing is possible.

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
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        if not self.active:
            return False

        if not self.owns_group(this_group) and not access_group.shareable:
            return False

        # must have a this_privilege greater than or equal to what we want to assign
        if UserGroupPrivilege.objects.filter(group=access_group,
                                             user=self,
                                             privilege__lte=this_privilege):
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

        # check for user error
        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        # check for user authorization
        if not self.active:
            raise HSAccessException("User is not active")

        if not self.owns_group(this_group) and not access_group.shareable:
            raise HSAccessException("User is not group owner and group is not shareable")

        # must have a this_privilege greater than or equal to what we want to assign
        if not UserGroupPrivilege.objects.filter(group=access_group,
                                                 user=self,
                                                 privilege__lte=this_privilege):
            raise HSAccessException("User has insufficient privilege over group")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        try:
            record = UserGroupPrivilege.objects.get(group=access_group,
                                                    user=access_user,
                                                    grantor=self)
            if record.privilege==PrivilegeCodes.OWNER \
                    and this_privilege!=PrivilegeCodes.OWNER \
                    and access_group.get_number_of_owners()==1:
                raise HSAccessException("Cannot remove last owner of group")

            record.privilege=this_privilege
            record.save()

        except UserGroupPrivilege.DoesNotExist:
            # create a new record
            UserGroupPrivilege(group=access_group,
                               user=access_user,
                               privilege=this_privilege,
                               grantor=self).save()

    def __handle_unshare_group_with_user(self, this_group, this_user, command=CommandCodes.CHECK):
        if not isinstance(this_group, Group):
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        if not self.active:
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
        if self.admin \
            or self.owns_group(this_group) \
            or access_user==self:
            # if there is a different owner,  we're fine
            if UserGroupPrivilege.objects \
                .filter(group=access_group,
                        privilege=PrivilegeCodes.OWNER) \
                .exclude(user=access_user):
                if command == CommandCodes.DO:
                    # then remove the record.
                    # this does not return an error if the object is not shared with the user
                    UserGroupPrivilege.objects.filter(group=access_group,
                                                      user=access_user).delete()
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


    def unshare_group_with_user(self, this_group, this_user):
        """
        Remove a user from a group by removing privileges.

        :param this_group: Group to be affected.
        :param this_user: User with whom to unshare group
        :return: Boolean

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
        return self.__handle_unshare_group_with_user(this_group, this_user, CommandCodes.CHECK)

    def __handle_undo_share_group_with_user(self, this_group, this_user, command=CommandCodes.CHECK, this_grantor=None):

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

            if not self.owns_group(this_group) and not self.admin:
                if command == CommandCodes.DO:
                    raise HSAccessException("Self must be owner or admin")
                else:
                    return False
        else: 
            access_grantor = self 

        if not self.active:
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
                                                      grantor=self)
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
        return self.__handle_undo_share_group_with_user(this_group, this_user, CommandCodes.DO, this_grantor)

    def can_undo_share_group_with_user(self, this_group, this_user, this_grantor=None):
        """
        Check whether we can remove a user from a group who was assigned by self.

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
        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess

        if self.admin or self.owns_group(this_group):

            if access_group.get_number_of_owners()>1:
                # print("Returning results for all undoes -- owners>1")
                # every possible undo is permitted, including self-undo
                return User.objects.filter(uaccess__held_groups=access_group)
            else:  # exclude sole owner from undo
                # print("Returning results for non-owner undos -- owners==1")
                # We need to return the users who are not owners, not the users who have privileges other than owner
                # all candidate undos
                # ids_shared = UserGroupPrivilege.objects.filter(group=access_group)\
                #                                    .values_list('user_id', flat=True).distinct()
                # # undoes that will remove sole owner
                # ids_owner = UserGroupPrivilege.objects.filter(group=access_group,
                #                                                  privilege=PrivilegeCodes.OWNER)\
                #                                    .values_list('user_id', flat=True).distinct()
                # # return difference
                # return User.objects.filter(uaccess__held_groups=access_group, uaccess__pk__in=ids_shared)\
                #                    .exclude(uaccess__pk__in=ids_owner)
                return User.objects.filter(uaccess__u2ugp__group=access_group)\
                                   .exclude(uaccess__u2ugp__group=access_group,
                                            uaccess__u2ugp__privilege=PrivilegeCodes.OWNER)
        else:
            if access_group.get_number_of_owners()>1:
                # self is grantor
                # OLD:  ids = UserGroupPrivilege.objects.filter(grantor=self, group=access_group)\
                # OLD:                                     .values_list('user_id')
                # OLD:  return User.objects.filter(uaccess__pk__in=ids)
                return User.objects.filter(uaccess__u2ugp__grantor=self, uaccess__u2ugp__group=access_group)
                # OLD:  According to the docs, the above code is compiled into one query, not two

            else:  # exclude sole owner from undo
                # OLD:  print("Returning results for non-owner undos -- owners==1")
                # OLD:  We need to return the users who are not owners, not the users who have privileges other than owner
                # OLD:  all candidate undos
                # OLD:  ids_shared = UserGroupPrivilege.objects.filter(grantor=self, group=access_group)\
                # OLD:                                         .values_list('user_id', flat=True).distinct()
                # OLD:  # undoes that will remove sole owner
                # OLD:  ids_owner = UserGroupPrivilege.objects.filter(grantor=self, group=access_group,
                # OLD:                                                privilege=PrivilegeCodes.OWNER)\
                # OLD:                                         .values_list('user_id', flat=True).distinct()
                # OLD:  # return difference
                # OLD:  return User.objects.filter(uaccess__held_groups=access_group, uaccess__pk__in=ids_shared)\
                # OLD:                     .exclude(uaccess__pk__in=ids_owner)

                # The following is a tricky query
                # a) I need to match for one record in u2ugp, which means that
                #    the matches have to be in the same filter()
                # b) I need to exclude matches with one extra attribute.
                #    Thus I must repeat attributes in the exclude.
                return User.objects.filter(uaccess__u2ugp__group=access_group,
                                           uaccess__u2ugp__grantor=self)\
                                   .exclude(uaccess__u2ugp__group=access_group,
                                            uaccess__u2ugp__grantor=self,
                                            uaccess__u2ugp__privilege=PrivilegeCodes.OWNER)

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
        # Users who can be removed fall into three catagories
        # a) self is admin: everyone.
        # b) self is group owner: everyone.
        # c) self is beneficiary: self only
        # Except that a user in the list cannot be the last owner.

        if not isinstance(this_group, Group): 
            raise HSAUsageException("Target is not a group")
        access_group = this_group.gaccess 

        if self.admin or self.owns_group(this_group):
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
        elif self in access_group.holding_users.all():
            if access_group.get_number_of_owners == 1:
                # if I'm not that owner
                if not UserGroupPrivilege.objects\
                        .filter(user=self, group=access_group, privilege=PrivilegeCodes.OWNER):
                    # this is a fancy way to return self as a QuerySet
                    # I can remove myself
                    return User.objects.filter(uaccess=self)
                else:
                    # I can't remove anyone
                    return User.objects.filter(uaccess=None)  # empty set
        else:
            return User.objects.filter(uaccess=None)  # empty set

    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: resources
    ##########################################
    ##########################################

    def create_resource(self, this_title):
        """
        Create a resource (debugging only)

        :param this_title: Title to use
        :return: Resource object
        """
        # create a resource object (by some means)
        r = GenericResource(title=this_title)
        r.save()
        # Bind to access object by reference
        a = ResourceAccess(resource=r)
        a.save()
        # first privilege must be unprotected to bootstrap 'share_with_user'
        UserResourcePrivilege(resource=a,
                              grantor=self,
                              user=self,
                              privilege=PrivilegeCodes.OWNER).save()
        return r

    def delete_resource(self, this_resource):
        """
        Delete a resource (debugging only)

        :param this_resource: Resource to delete.
        :return: None
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        if self.admin or self.owns_resource(this_resource):
            # delete all references to group_id
            UserResourcePrivilege.objects.filter(resource=access_resource).delete()
            GroupResourcePrivilege.objects.filter(resource=access_resource).delete()
            access_resource.delete() # derived resource object
            this_resource.delete() # original resource object 
        else:
            raise HSAccessException("User must own resource")

    ##########################################
    # public and discoverable resources
    ##########################################

    @staticmethod
    def get_discoverable_resources():
        """
        Get a list of discoverable resources

        :return: List of discoverable resource objects
        """
        return GenericResource.objects.filter(Q(raccess__discoverable=True) | Q(raccess__public=True))

    @staticmethod
    def get_public_resources():
        """
        Get a list of public resources.

        :return: List of public resource objects.
        """
        return GenericResource.objects.filter(raccess__public=True)

    ##########################################
    # held and owned resources
    ##########################################

    def get_held_resources(self):
        """
        Get a list of resources held by user.

        :return: List of resource objects accessible (in any form) to user.
        """
        return GenericResource.objects.filter(Q(raccess__holding_users=self) | Q(raccess__holding_groups__members=self))

    def get_number_of_held_resources(self):
        """
        Get the number of resources held by user.

        :return: Integer number of resources accessible for this user.
        """
        # utilize simpler join-free query that that of get_held_resources()
        return ResourceAccess.objects.filter(Q(holding_users=self) | Q(holding_groups__members=self)).count()

    def get_owned_resources(self):
        """
        Get a list of resources owned by user.

        :return: List of resource objects owned by this user.
        """
        # OLD:  ids = UserResourcePrivilege.objects.filter(user=self, privilege=PrivilegeCodes.OWNER)\
        # OLD:      .values_list('resource_id', flat=True).distinct()
        # OLD:  return Resource.objects.filter(raccess__pk__in=ids)
        # OLD:  According to the docs, the above is compiled into one query rather than two
        return GenericResource.objects.filter(raccess__r2urp__user=self,
                                              raccess__r2urp__privilege=PrivilegeCodes.OWNER).distinct()


    def get_number_of_owned_resources(self):
        """
        Get number of resources owned by self.

        :return: Integer number of resources owned by user.

        This is a separate procedure, rather than get_owned_resources().count(), due to performance concerns.
        """
        # This is a join-free query; get_owned_resources includes a join.
        return self.get_owned_resources().count()
        # OLD:  return UserResourcePrivilege.objects.filter(user=self, privilege=PrivilegeCodes.OWNER)\
        # OLD:      .values_list('resource_id', flat=True).distinct().count()

    def get_editable_resources(self):
        """
        Get a list of resources that can be edited by user.

        :return: List of resource objects that can be edited  by this user.
        """

        return GenericResource.objects.filter(raccess__r2urp__user=self, raccess__immutable=False,
                                              raccess__r2urp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    #############################################
    # Check access permissions for self (user)
    #############################################

    def owns_resource(self, this_resource):
        """
        Boolean: is the user an owner of this resource?

        :param self: user on which to report.
        :return: True if user is an owner

        Note that the fact that someone owns a resource is not sufficient proof that
        one has permission to change it, because resource flags can override the raw
        privilege. It is thus necessary to check that one can change something
        explicitly, using UserAccess.can_change_resource()
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege=PrivilegeCodes.OWNER,
                                                user=self):
            return True
        else:
            return False

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
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        if not self.active:
            return False

        if access_resource.immutable:
            return False

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege__lte=PrivilegeCodes.CHANGE,
                                                user=self):
            return True

        if GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                 privilege__lte=PrivilegeCodes.CHANGE,
                                                 group__members=self):
            return True

        return False

    def can_change_resource_flags(self, this_resource):
        """
        Whether self can change resource flags.

        :param this_resource: Resource to check.
        :return: True if user can set flags.

        This is not enforced. It is up to the programmer to obey this restriction.
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        return self.active and (self.admin or self.owns_resource(this_resource))

    def can_view_resource(self, this_resource):
        """
        Whether user can view this resource

        :param this_resource: Resource to check
        :return: True if user can view this resource.

        Note that one can view resources that are public, that one does not own.
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        if not self.active:
            return False

        if access_resource.public:
            return True

        if UserResourcePrivilege.objects.filter(resource=access_resource,
                                                privilege__lte=PrivilegeCodes.VIEW,
                                                user=self):
            return True

        if GroupResourcePrivilege.objects.filter(resource=access_resource,
                                                 privilege__lte=PrivilegeCodes.VIEW,
                                                 group__members=self):
            return True

        return False

    def can_delete_resource(self, this_resource):
        """
        Whether user can delete a resource

        :param this_resource: Resource to check.
        :return: True if user can delete the resource.
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess 

        return self.active and (self.admin or self.owns_resource(this_resource))

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
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not self.active:
            return False

        # access control logic: Can change privilege if
        #   Admin
        #   Owner
        #   Privilege for self
        whom_priv = access_resource.get_combined_privilege(self.user)

        # check for user authorization
        if self.admin:
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
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if this_privilege==PrivilegeCodes.OWNER:
            return False

        # check for user authorization
        # a) user must have privilege over resource
        # b) user must be in the group
        if not self.can_share_resource(this_resource, this_privilege):
            return False

        if self not in this_group.members:
            return False

        return True

    def __handle_undo_share_resource_with_group(self, this_resource, this_group, command=CommandCodes.CHECK, this_grantor=None):
        # first check for usage error
        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if command != CommandCodes.CHECK and command != CommandCodes.DO:
            raise HSAUsageException("Invalid command code")

        # handle optional grantor parameter that scopes owner-based unshare to one share.
        if this_grantor is not None and this_grantor.uaccess != self:
            if not isinstance(this_grantor, User):
                raise HSAUsageException("Grantor is not a user")

            access_grantor = this_grantor.uaccess

            if not self.owns_resource(this_resource) and not self.admin:
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
            access_grantor = self

        # print('resource='+this_resource.title+', group='+this_group.name+', grantor='+access_grantor.user.first_name)
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

    def undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        """
        Remove resource privileges self-granted to a group.

        :rtype: Boolean
        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: None

        This tries to remove one user access record for "this_group" and "this_resource"
        if grantor is self. If this_grantor is specified, that is utilized as grantor as long as
        self is owner or admin.
        """
        return self.__handle_undo_share_resource_with_group(this_resource,
                                                            this_group,
                                                            CommandCodes.DO,
                                                            this_grantor)

    def can_undo_share_resource_with_group(self, this_resource, this_group, this_grantor=None):
        """
        Check whether one can remove resource privileges self-granted to a group.

        :rtype: Boolean
        :param this_resource: resource for which to undo share.
        :param this_group: group with which to unshare resource
        :return: None

        This checks whether one can remove one user access record for "this_group" and "this_resource"
        if grantor is self. If this_grantor is specified, that is utilized as the grantor as long as
        self is owner or admin.
        """
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

        # check for user error

        if not isinstance(this_user, User):
            raise HSAUsageException("Grantee is not a user")
        access_user = this_user.uaccess

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        # this is parallel to can_share_resource_with_user(this_resource, this_privilege)

        if not self.active:
            raise HSAccessException("Requester is not an active user")

        # access control logic: Can change privilege if
        #   Admin
        #   Self-set permission
        #   Owner
        #   Non-owner and shareable
        whom_priv = access_resource.get_combined_privilege(self.user)

        # check for user authorization

        if self.admin:
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
                                                         grantor=self)
            if record.privilege==PrivilegeCodes.OWNER \
                    and this_privilege!=PrivilegeCodes.OWNER \
                    and access_resource.get_number_of_owners()==1:
                raise HSAccessException("Cannot remove last owner of resource")

            # record.start=timezone.now() # now automatically set
            record.privilege=this_privilege
            record.save()

        except UserResourcePrivilege.DoesNotExist:
            # create a new record
            UserResourcePrivilege(resource=access_resource,
                                  user=access_user,
                                  privilege=this_privilege,
                                  grantor=self).save()


    def __handle_unshare_resource_with_user(self, this_resource, this_user, command=CommandCodes.CHECK):

        """
        Remove a user from a resource by removing privileges.

        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :param command: command code to perform
        :return: Boolean

        This removes a user "this_user" from resource access to "this_resource" if one of the following is true:

            * self is an administrator.

            * self owns the group.

            * requesting user is the grantee of resource access.

        *and* removing the user will not lead to a resource without an owner.

        There is no provision for revoking lower-level permissions for an owner.
        If a user is a sole owner and holds other privileges, this call will not remove them.
        """

        # first check for usage error
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
        if self.admin \
                or access_resource.get_combined_privilege(self.user) == PrivilegeCodes.OWNER \
                or access_user == self:
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

    def unshare_resource_with_user(self, this_resource, this_user):
        """
        Unshare a resource with a specific user, removing all privilege for that user

        :param this_resource: Resource to unshare
        :param this_user:  User wich whom to unshare it.
        :return: True if it is unshared successfully.
        """
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
        return self.__handle_unshare_resource_with_user(this_resource, this_user, CommandCodes.CHECK)

    def __handle_undo_share_resource_with_user(self, this_resource, this_user, command=CommandCodes.CHECK, this_grantor=None):
        """
        Remove a self-granted privilege from a user.

        :param this_resource: resource to unshare
        :param this_user: user with which to unshare resource
        :return: None

        This removes a user "this_user" from resource access to "this_resource" if self granted the privilege,
        *and* removing the user will not lead to a resource without an owner.
        """

        # first check for usage error
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

            if not self.owns_resource(this_resource) and not self.admin:
                if command == CommandCodes.DO:
                    raise HSAccessException("Self must be owner or admin")
                else:
                    return False
        else: 
            access_grantor = self 

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

    def undo_share_resource_with_user(self, this_resource, this_user, this_grantor=None):
        return self.__handle_undo_share_resource_with_user(this_resource, this_user, CommandCodes.DO, this_grantor)

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

        # check for user error
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if not isinstance(this_group, Group):
            raise HSAUsageException("Grantee is not a group")
        access_group = this_group.gaccess

        if this_privilege==PrivilegeCodes.OWNER:
            raise HSAccessException("Groups cannot own resources")
        if this_privilege<PrivilegeCodes.OWNER or this_privilege>PrivilegeCodes.VIEW: 
            raise HSAccessException("Privilege level not valid")

        # check for user authorization
        if not self.can_share_resource(this_resource, this_privilege):
            raise HSAccessException("User has insufficient sharing privilege over resource")

        if self not in access_group.members.all():
            raise HSAccessException("User is not a member of the group")

        # user is authorized and privilege is appropriate
        # proceed to change the record if present

        # This logic implicitly limits one to one record per resource and requester.
        try:
            record = GroupResourcePrivilege.objects.get(resource=access_resource,
                                                        group=access_group,
                                                        grantor=self)

            # record.start=timezone.now() # now automatically set
            record.privilege=this_privilege
            record.save()

        except GroupResourcePrivilege.DoesNotExist:
            # create a new record
            GroupResourcePrivilege(resource=access_resource,
                                   group=access_group,
                                   privilege=this_privilege,
                                   grantor=self).save()


    def __handle_unshare_resource_with_group(self, this_resource, this_group, command=CommandCodes.CHECK):
        # first check for usage error

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
        if self.admin \
                or self.owns_resource(this_resource) \
                or self.owns_group(this_group):

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
        return self.__handle_unshare_resource_with_group(this_resource, this_group, CommandCodes.DO)

    def can_unshare_resource_with_group(self, this_resource, this_group):
        """
        Check whether one can unshare a resource with a group.

        :param this_resource: resource to be protected.
        :param this_group: group with which to unshare resource.
        :return: None

        Unsharing will remove a user "this_group" from access to "this_resource" if one of the following is true:

            * self is an administrator.
            * self owns the resource.
            * self owns the group.

        This routine returns False exactly when unshare_resource_with_group will raise an exception.
        """
        return self.__handle_unshare_resource_with_group(this_resource, this_group, CommandCodes.CHECK)

    ##########################################
    # users whose access could be undone by self
    ##########################################
    def get_resource_undo_users(self, this_resource):
        """
        Get a list of users to whom self granted access

        :param this_resource: resource to check.
        :return: list of users granted access by self.
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if self.admin or self.owns_resource(this_resource):

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
                # OLD:  ids = UserResourcePrivilege.objects.filter(grantor=self, resource=access_resource)\
                # OLD:                                     .values_list('user_id')
                # OLD:
                # OLD:  return User.objects.filter(uaccess__pk__in=ids)
                return User.objects.filter(uaccess__u2urp__grantor=self,
                                           uaccess__u2urp__resource=access_resource).distinct()
                # OLD:  According to the docs, the above code is compiled into one query, not two

            else:  # exclude sole owner from undo
                # OLD:  #  print("Returning results for non-owner undos -- owners==1")
                # OLD:  # We need to return the users who are not owners, not the users who have privileges other than owner
                # OLD:  # all candidate undos
                # OLD:  ids_shared = UserResourcePrivilege.objects.filter(grantor=self, resource=access_resource)\
                # OLD:                                     .values_list('user_id', flat=True).distinct()
                # OLD:  # undoes that will remove sole owner
                # OLD:  ids_owner = UserResourcePrivilege.objects.filter(grantor=self, resource=access_resource,
                # OLD:                                                   privilege=PrivilegeCodes.OWNER)\
                # OLD:                                     .values_list('user_id', flat=True).distinct()
                # OLD:  # return difference
                # OLD:  return User.objects.filter(uaccess__held_resources=access_resource, uaccess__pk__in=ids_shared)\
                # OLD:                     .exclude(uaccess__pk__in=ids_owner)
                return User.objects.filter(uaccess__u2urp__grantor=self,
                                           uaccess__u2urp__resource=access_resource)\
                                   .exclude(uaccess__u2urp__grantor=self,
                                            uaccess__u2urp__resource=access_resource,
                                            uaccess__u2urp__privilege=PrivilegeCodes.OWNER).distinct()

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

        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if self.admin or self.owns_resource(this_resource):
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
        elif self in access_resource.holding_users.all():
            return User.objects.filter(uaccess=self)
        else:
            return User.objects.filter(uaccess=None)  # empty set

    def get_resource_undo_groups(self, this_resource):
        """
        Get a list of users to whom self granted access

        :param this_resource: resource to check.
        :return: list of users granted access by self.

        A user can undo a privilege if

            1. That privilege was assigned by this user.
            2. User owns the resource
            3. User owns the group -- *not implemented*
            4. User is an administrator
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        if self.admin or self.owns_resource(this_resource):
            # all groups with resource privilege
            # OLD: ids = GroupResourcePrivilege.objects.filter(resource=access_resource)\
            # OLD:     .values_list('group_id', flat=True).distinct()
            return Group.objects.filter(gaccess__held_resources=access_resource).distinct()
        else:  #  privilege only for grantor
            # OLD: ids = GroupResourcePrivilege.objects.filter(resource=access_resource, grantor=self)\
            # OLD:     .values_list('group_id', flat=True).distinct()
            return Group.objects.filter(gaccess__g2grp__resource=access_resource,
                                        gaccess__g2grp__grantor=self).distinct()
        # OLD: return Group.objects.filter(gaccess__pk__in=ids)
        # OLD: According to the docs, the above code is compiled into one query, not two

    def get_resource_unshare_groups(self, this_resource):
        """
        Get a list of groups who could be unshared from this group.

        :param this_resource: resource to check.
        :return: list of users who could be removed by self.

        This is a list of groups for which unshare_resource_with_group will work for this user.
        """
        if not isinstance(this_resource, GenericResource):
            raise HSAUsageException("Target is not a resource")
        access_resource = this_resource.raccess

        # Users who can be removed fall into three catagories
        # a) self is admin: everyone with access.
        # b) self is resource owner: everyone with access.
        # c) self is group owner: only for owned groups

        # if user is administrator or owner, then return all groups with access.

        if self.admin or self.owns_resource(this_resource):
            # all shared groups
            return Group.objects.filter(gaccess__held_resources=access_resource)
        else:
            # groups with access that the user owns.
            # OLD: ids = UserGroupPrivilege.objects.filter(user=self, privilege=PrivilegeCodes.OWNER)\
            # OLD:     .values_list('group_id', flat=True).distinct()
            # OLD: return Group.objects.filter(gaccess__held_resources=access_resource, gaccess__pk__in=ids)
            return Group.objects.filter(gaccess__g2ugp__user=self,
                                        gaccess__g2ugp__privilege=PrivilegeCodes.OWNER).distinct()

class GroupAccess(models.Model):
    """ Avoid real Django Group for testing and development
    """
    # title = models.CharField(max_length=200)
    # don't store name metadata in access control

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
        # return self.get_held_resources().count()
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
        # OLD: ids = UserGroupPrivilege.objects.filter(group=self, privilege=PrivilegeCodes.OWNER)\
        # OLD:     .values_list('user_id', flat=True).distinct()
        # OLD: return User.objects.filter(uaccess__pk__in=ids).all()
        return User.objects.filter(uaccess__u2ugp__group=self,
                                   uaccess__u2ugp__privilege=PrivilegeCodes.OWNER).distinct()
        # According to the docs, the above code is compiled into one query, not two

        # the following should work but does not
        # return self.members.filter(usergroupprivilege__privilege=PrivilegeCodes.OWNER)
        # (it does work for one-one relationships!)

    def get_number_of_owners(self):
        """
        Return number of owners for a group.

        :return: Integer

        This eliminates duplicates due to multiple invitations.
        """
        return self.get_owners().count()
        # UserGroupPrivilege.objects.filter(group=self,
        #                                   privilege=PrivilegeCodes.OWNER)\
        #     .values_list('user_id', flat=True).distinct().count()

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
    """ Simple resource model for debugging incorporates new access control
    """
    #############################################
    # model variables
    #############################################

    resource = models.OneToOneField('GenericResource',
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
        # OLD: ids = UserResourcePrivilege.objects.filter(resource=self,
        # OLD:                                            privilege__lte=PrivilegeCodes.VIEW)\
        # OLD:         .values_list('user_id', flat=True).distinct()
        # OLD: return User.objects.filter(uaccess__id__in=ids).all()
        return User.objects.filter(uaccess__u2urp__resource=self,
                                   uaccess__u2urp__privilege__lte=PrivilegeCodes.VIEW).distinct()

    @property
    def edit_users(self):
        # OLD: ids = UserResourcePrivilege.objects.filter(resource=self,
        # OLD:                                            privilege__lte=PrivilegeCodes.CHANGE)\
        # OLD:        .values_list('user_id', flat=True).distinct()
        # OLD: return User.objects.filter(uaccess__id__in=ids).all()
        return User.objects.filter(uaccess__u2urp__resource=self,
                                   uaccess__u2urp__privilege__lte=PrivilegeCodes.CHANGE).distinct()
    @property
    def view_groups(self):
        # OLD:  ids = GroupResourcePrivilege.objects.filter(resource=self,
        # OLD:                                              privilege__lte=PrivilegeCodes.VIEW)\
        # OLD:          .values_list('group_id', flat=True).distinct()
        # OLD:  return User.objects.filter(uaccess__id__in=ids).all()
        return Group.objects.filter(gaccess__g2grp__resource=self,
                                    gaccess__g2grp__privilege__lte=PrivilegeCodes.VIEW).distinct()

    @property
    def edit_groups(self):
        # OLD:  ids = GroupResourcePrivilege.objects.filter(resource=self,
        # OLD:                                              privilege__lte=PrivilegeCodes.CHANGE)\
        # OLD:          .values_list('group_id', flat=True).distinct()
        # OLD:  return User.objects.filter(uaccess__id__in=ids).all()
        return Group.objects.filter(gaccess__g2grp__resource=self,
                                    gaccess__g2grp__privilege__lte=PrivilegeCodes.CHANGE).distinct()

    @property
    def owners(self):
        # OLD:  ids = UserResourcePrivilege.objects.filter(resource=self,
        # OLD:                                             privilege=PrivilegeCodes.OWNER)\
        # OLD:          .values_list('user_id', flat=True).distinct()
        # OLD:  return User.objects.filter(uaccess__id__in=ids).all()
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
        # OLD:  ids = UserResourcePrivilege.objects.filter(resource=self,
        # OLD:                                             privilege=PrivilegeCodes.OWNER)\
        # OLD:      .values_list('user_id', flat=True).distinct()
        # OLD:  return User.objects.filter(uaccess__id__in=ids).all()
        # OLD:  # According to the docs, the above code is compiled into one query, not two
        return User.objects.filter(uaccess__u2urp__privilege=PrivilegeCodes.OWNER,
                                   uaccess__u2urp__resource=self)

    def get_number_of_owners(self):
        """
        Get number of owners for the current resource.

        :return: Integer number of owners

        This must eliminate duplicates due to the possibility of
        multiple owner records for the same resource and user.
        """
        # OLD:  return UserResourcePrivilege.objects.filter(resource=self,
        # OLD:                                              privilege=PrivilegeCodes.OWNER)\
        # OLD:      .values_list('user_id', flat=True).distinct().count()
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
        :return: integer privilege 1-4

        This reports combined privilege of a user due to user permissions and group permissions, but does
        not account for resource flags.

        The privilege codes returned include

            * 1 or PrivilegeCodes.OWNER:
                the user owns the object.

            * 2 or PrivilegeCodes.CHANGE:
                the user can change the content of the object but not its state.

            * 3 or PrivilegeCodes.VIEW:
                the user can view but not change the object.

            * 4 or PrivilegeCodes.NONE:
                the user has no privilege over the object.

        Note that this privilege is the privilege that the user holds, not the privilege
        in effect due to flags.  See "get_effective_privilege" to account for flags.
        """
        # print("all user privileges:")
        # for i in UserResourcePrivilege.objects.all():
        #     u = i.user
        #     p = i.privilege
        #     r = i.resource
        #     g = i.grantor
        #     print("resource:", r.title, ", user:", u.name, ", privilege:", p, ", grantor:", g.name)

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

        # user_groups = UserGroupPrivilege.objects.filter(user=this_user)
        # print("groups are:")
        # for i in user_groups:
        #     u = i.user
        #     p = i.privilege
        #     r = i.group
        #     g = i.grantor
        #     print("group:", r.title, ", user:", u.name, ", privilege:", p, ", grantor:", g.name)

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
        :return: integer privilege 1-4

        This reports the privilege arising from group membership only.
        The privilege codes returned include

            * 1 or PrivilegeCodes.OWNER:
                the user owns the object.

            * 2 or PrivilegeCodes.CHANGE:
                the user can change the content of the object but not its state.

            * 3 or PrivilegeCodes.VIEW:
                the user can view but not change the object.

            * 4 or PrivilegeCodes.NONE:
                the user has no privilege over the object.

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
        and group privilege as well as resource flags. Return values include:

            * 1 or PrivilegeCodes.OWNER:
                the user owns the object.

            * 2 or PrivilegeCodes.CHANGE:
                the user can change the content of the object but not its state.

            * 3 or PrivilegeCodes.VIEW:
                the user can view but not change the object.

            * 4 or PrivilegeCodes.NONE:
                the user has no privilege over the object.

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


# this should be used as the page processor for anything with pagepermissionsmixin
# page_processor_for(MyPage)(ga_resources.views.page_permissions_page_processor)
def page_permissions_page_processor(request, page):
    cm = page.get_content_model()
    can_change_resource_flags = False
    if request.user.is_authenticated():
        if request.user.uaccess.can_change_resource_flags(cm):
            can_change_resource_flags = True

    owners = set(cm.raccess.owners.all())
    editors = set(cm.raccess.edit_users.all()) - owners
    viewers = set(cm.raccess.view_users.all()) - editors - owners

    return {
        'resource_type': cm._meta.verbose_name,
        'bag': cm.bags.first(),
        'groups': Group.objects.all(),
        "edit_groups": set(cm.raccess.edit_groups.all()),
        "view_groups": set(cm.raccess.view_groups.all()),
        "edit_users": editors,
        "view_users": viewers,
        "owners": owners,
        "can_change_resource_flags": can_change_resource_flags
    }


class AbstractMetaDataElement(models.Model):
    term = None

    object_id = models.PositiveIntegerField()
    # see the following link the reason for having the related_name setting for the content_type attribute
    # https://docs.djangoproject.com/en/1.6/topics/db/models/#abstract-related-name
    content_type = models.ForeignKey(ContentType, related_name="%(app_label)s_%(class)s_related")
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    @property
    def metadata(self):
        return self.content_object

    @classmethod
    def create(cls, **kwargs):
        raise NotImplementedError("Please implement this method")

    @classmethod
    def update(cls, element_id, **kwargs):
        raise NotImplementedError("Please implement this method")

    # could not name this method as 'delete' since the parent 'Model' class has such a method
    @classmethod
    def remove(cls, element_id):
        raise NotImplementedError("Please implement this method")

    class Meta:
        abstract = True

# Adaptor class added for Django inplace editing to honor HydroShare user-resource permissions
class HSAdaptorEditInline(object):
    @classmethod
    def can_edit(cls, adaptor_field):
        #from hs_core.views.utils import authorize
        user = adaptor_field.request.user
        can_edit = False
        if user.is_anonymous():
            pass
        elif user.is_superuser:
            can_edit = True
        else:
            obj = adaptor_field.obj
            cm = obj.get_content_model()
            #_, can_edit, _ = authorize(adaptor_field.request, res_id, edit=True, full=True) - need to know res_id
            can_edit = (user in set(cm.edit_users.all())) or (len(set(cm.edit_groups.all()).intersection(set(user.groups.all()))) > 0)
        return can_edit

class ExternalProfileLink(models.Model):
    type = models.CharField(max_length=50)
    url = models.URLField()

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ("type", "url", "object_id")

class Party(AbstractMetaDataElement):
    description = models.URLField(null=True, blank=True, validators=[validate_user_url])
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    external_links = generic.GenericRelation(ExternalProfileLink)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

    @classmethod
    def create(cls,**kwargs):
        element_name = cls.__name__
        if 'name' in kwargs:
            if not isinstance(kwargs['content_object'], CoreMetaData) and not issubclass(kwargs['content_object'], CoreMetaData):
                raise ValidationError("%s metadata element can't be created for metadata type:%s" %(element_name, type(kwargs['content_object'])))

            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            if element_name == 'Creator':
                party = Creator.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).last()
                creator_order = 1
                if party:
                    creator_order = party.order + 1
                if len(kwargs['name'].strip()) == 0:
                    raise ValidationError("Invalid name for the %s." % element_name.lower())

                party = Creator.objects.create(name=kwargs['name'], order=creator_order, content_object=metadata_obj)
            else:
                party = Contributor.objects.create(name=kwargs['name'], content_object=metadata_obj)

            if 'profile_links' in kwargs:
                links = kwargs['profile_links']
                for link in links:
                    cls._create_profile_link(party, link)

            for key, value in kwargs.iteritems():
                if key in ('description', 'organization', 'email', 'address', 'phone', 'homepage'):
                    setattr(party, key, value)

            party.save()
            return party
        else:
            raise ValidationError("Name for the %s is missing." % element_name.lower())

    @classmethod
    def update(cls, element_id, **kwargs):
        element_name = cls.__name__
        if element_name == 'Creator':
            party = Creator.objects.get(id=element_id)
        else:
            party = Contributor.objects.get(id=element_id)

        if party:
            if 'name' in kwargs:
                party.name = kwargs['name']

            if 'description' in kwargs:
                party.description = kwargs['description']

            if 'organization' in kwargs:
                party.organization = kwargs['organization']

            if 'email' in kwargs:
                party.email = kwargs['email']

            if 'address' in kwargs:
                party.address = kwargs['address']

            if 'phone' in kwargs:
                party.phone = kwargs['phone']

            if 'homepage' in kwargs:
                party.homepage = kwargs['homepage']

            if 'researcherID' in kwargs:
                party.researcherID = kwargs['researcherID']

            if 'researchGateID' in kwargs:
                party.researchGateID = kwargs['researchGateID']

            # updating the order of a creator needs updating the order attribute of all other creators
            # of the same resource
            if 'order' in kwargs:
                if isinstance(party, Creator):
                    if kwargs['order'] <= 0:
                        kwargs['order'] = 1

                    if party.order != kwargs['order']:
                        resource_creators = Creator.objects.filter(object_id=party.object_id, content_type__pk=party.content_type.id).all()

                        if kwargs['order'] > len(resource_creators):
                            kwargs['order'] = len(resource_creators)

                        for res_cr in resource_creators:
                            if party.order > kwargs['order']:
                                if res_cr.order < party.order and not res_cr.order < kwargs['order']:
                                    res_cr.order += 1
                                    res_cr.save()

                            else:
                                if res_cr.order > party.order:
                                    res_cr.order -= 1
                                    res_cr.save()


                        party.order = kwargs['order']

            #either create or update external profile links
            if 'profile_links' in kwargs:
                links = kwargs['profile_links']
                for link in links:
                    if 'link_id' in link: # need to update an existing profile link
                        cls._update_profile_link(party, link)
                    elif 'type' in link and 'url' in link:  # add a new profile link
                        cls._create_profile_link(party, link)
            party.save()
        else:
            raise ObjectDoesNotExist("No %s was found for the provided id:%s" % (element_name, kwargs['id']))

    @classmethod
    def remove(cls, element_id):
        element_name = cls.__name__
        if element_name == 'Creator':
            party = Creator.objects.get(id=element_id)
        else:
            party = Contributor.objects.get(id=element_id)

        # if we are deleting a creator, then we have to update the order attribute of remaining
        # creators associated with a resource
        if party:
            # make sure we are not deleting all creators of a resource
            if isinstance(party, Creator):
                if Creator.objects.filter(object_id=party.object_id, content_type__pk=party.content_type.id).count()== 1:
                    raise ValidationError("The only creator of the resource can't be deleted.")

                creators_to_update = Creator.objects.filter(
                    object_id=party.object_id, content_type__pk=party.content_type.id).exclude(order=party.order).all()

                for cr in creators_to_update:
                    if cr.order > party.order:
                        cr.order -= 1
                        cr.save()
            party.delete()
        else:
            raise ObjectDoesNotExist("No %s element was found for id:%d." % (element_name, element_id))

    @classmethod
    def _create_profile_link(cls, party, link):
        if 'type' in link and 'url' in link:
            # check that the type is unique for the party
            if party.external_links.filter(type=link['type']).count() > 0:
                raise ValidationError("External profile link type:%s already exists "
                                      "for this %s" % (link['type'], type(party).__name__))

            if party.external_links.filter(url=link['url']).count() > 0:
                raise ValidationError("External profile link url:%s already exists "
                                      "for this %s" % (link['url'], type(party).__name__))

            p_link = ExternalProfileLink(type=link['type'], url=link['url'], content_object=party)
            p_link.save()
        else:
            raise ValidationError("Invalid %s profile link data." % type(party).__name__)

    @classmethod
    def _update_profile_link(cls, party, link):
        """
        if the link dict contains only key 'link_id' then the link will be deleted
        otherwise the link will be updated
        """
        p_link = ExternalProfileLink.objects.get(id=link['link_id'])
        if p_link:
            if not 'type' in link and not 'url' in link:
                # delete the link
                p_link.delete()
            else:
                if 'type' in link:
                    # check that the type is unique for the party
                    if p_link.type != link['type']:
                        if party.external_links.filter(type=link['type']).count() > 0:
                            raise ValidationError("External profile link type:%s "
                                                  "already exists for this %s" % (link['type'], type(party).__name__))
                        else:
                            p_link.type = link['type']
                if 'url' in link:
                    # check that the url is unique for the party
                    if p_link.url != link['url']:
                        if party.external_links.filter(url=link['url']).count() > 0:
                            raise ValidationError("External profile link url:%s already exists "
                                                  "for this %s" % (link['url'], type(party).__name__))
                        else:
                            p_link.url = link['url']

                p_link.save()
        else:
            raise ObjectDoesNotExist("%s external link does not exist "
                                     "for ID:%s" % (type(party).__name__,link['link_id']))

class Contributor(Party):
    term = 'Contributor'



# Example of repeatable metadata element
class Creator(Party):
    term = "Creator"
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']


class Description(AbstractMetaDataElement):
    term = 'Description'
    abstract = models.TextField()

    def __unicode__(self):
        return self.abstract

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'abstract' in kwargs:

            # no need to check if a description element already exists
            # the Meta settings 'unique_together' will enforce that we have only one description element per resource
            return Description.objects.create(**kwargs)

        else:
            raise ValidationError("Abstract of the description element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        description = Description.objects.get(id=element_id)
        if description:
            if 'abstract' in kwargs:
                if len(kwargs['abstract'].strip()) > 0:
                    description.abstract = kwargs['abstract']
                    description.save()
                else:
                    raise ValidationError('A value for the description/abstract element is missing.')
            else:
                raise ValidationError('A value for description/abstract element is missing.')
        else:
            raise ObjectDoesNotExist("No description/abstract element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Description element of a resource can't be deleted.")

class Title(AbstractMetaDataElement):
    term = 'Title'
    value = models.CharField(max_length=300)

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            return Title.objects.create(**kwargs)

        else:
            raise ValidationError("Value of the title element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        title = Title.objects.get(id=element_id)
        if title:
            if 'value' in kwargs:
                title.value = kwargs['value']
                title.save()
                # This way of updating the resource title field does not work
                # so updating code is in in resource.py
                # res = title.content_object.resource
                # res.title = title.value
                # res.save()
            else:
                raise ValidationError('Value for title is missing.')
        else:
            raise ValidationError("No title element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Title element of a resource can't be deleted.")

class Type(AbstractMetaDataElement):
    term = 'Type'
    url = models.URLField()

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'url' in kwargs:
            return Type.objects.create(**kwargs)
        else:
            raise ValidationError("URL of the type element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        type = Type.objects.get(id=element_id)
        if type:
            if 'url' in kwargs:
                type.url = kwargs['url']
                type.save()
            else:
                raise ValidationError('URL for type element is missing.')
        else:
            raise ObjectDoesNotExist("No type element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Type element of a resource can't be deleted.")

class Date(AbstractMetaDataElement):
    DATE_TYPE_CHOICES=(
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('valid', 'Valid'),
        ('available', 'Available'),
        ('published', 'Published')
    )

    term = 'Date'
    type = models.CharField(max_length=20, choices=DATE_TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    @classmethod
    def create(cls, **kwargs):
        if 'type' in kwargs:
            # check the type doesn't already exists - we allow only one date type per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            dt = Date.objects.filter(type= kwargs['type'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if dt:
                raise ValidationError('Date type:%s already exists' % kwargs['type'])
            if not kwargs['type'] in ['created', 'modified', 'valid', 'available', 'published']:
                raise ValidationError('Invalid date type:%s' % kwargs['type'])

            if kwargs['type'] == 'published':
                if not metadata_obj.resource.published_and_frozen:
                    raise ValidationError("Resource is not published yet.")

            if kwargs['type'] == 'available':
                if not metadata_obj.resource.public:
                    raise ValidationError("Resource has not been shared yet.")

            if 'start_date' in kwargs:
                try:
                    start_dt = parser.parse(str(kwargs['start_date']))
                except TypeError:
                    raise TypeError("Not a valid date value.")
            else:
                raise ValidationError('Date value is missing.')

            # end_date is used only for date type 'valid'
            if kwargs['type'] == 'valid':
                if 'end_date' in kwargs:
                    try:
                        end_dt = parser.parse(str(kwargs['end_date']))
                    except TypeError:
                        raise TypeError("Not a valid end date value.")
                    dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, end_date=end_dt, content_object=metadata_obj)
                else:
                    dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, content_object=metadata_obj)
            else:
                dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, content_object=metadata_obj)

            return dt

        else:
            raise ValidationError("Type of date element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        dt = Date.objects.get(id=element_id)
        if dt:
            if 'start_date' in kwargs:
                try:
                    start_dt = parser.parse(str(kwargs['start_date']))
                except TypeError:
                    raise TypeError("Not a valid date value.")
                if dt.type == 'created':
                    raise ValidationError("Resource creation date can't be changed")
                elif dt.type == 'modified':
                    dt.start_date = now().isoformat()
                    dt.save()
                elif dt.type == 'valid':
                    if 'end_date' in kwargs:
                        try:
                            end_dt = parser.parse(str(kwargs['end_date']))
                        except TypeError:
                            raise TypeError("Not a valid date value.")
                        dt.start_date = start_dt
                        dt.end_date = end_dt
                        dt.save()
                    else:
                        dt.start_date = start_dt
                        dt.save()
                else:
                    dt.start_date = start_dt
                    dt.save()
            elif dt.type == 'modified':
                dt.start_date = now().isoformat()
                dt.save()
            else:
                raise ValidationError("Date value is missing.")
        else:
            raise ObjectDoesNotExist("No date element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        dt = Date.objects.get(id=element_id)
        if dt:
            if dt.type in ['created', 'modified']:
                raise ValidationError("Date element of type:%s can't be deleted." % dt.type)

            dt.delete()
        else:
            raise ObjectDoesNotExist("No date element was found for id:%d." % element_id)

class Relation(AbstractMetaDataElement):
    SOURCE_TYPES= (
        ('isPartOf', 'Part Of'),
        ('isExecutedBy', 'Executed By'),
        ('isCreatedBy', 'Created By'),
        ('isVersionOf', 'Version Of'),
        ('isDataFor', 'Data For'),
        ('cites', 'Cites'),
    )

    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.CharField(max_length=500)

    @classmethod
    def create(cls, **kwargs):
        if 'type' in kwargs:
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            rel = Relation.objects.filter(type= kwargs['type'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if rel:
                raise ValidationError('Relation type:%s already exists.' % kwargs['type'])
            if 'value' in kwargs:
                return Relation.objects.create(type=kwargs['type'], value=kwargs['value'], content_object=metadata_obj)

            else:
                raise ValidationError('Value for relation element is missing.')
        else:
            raise ObjectDoesNotExist("Type of relation element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        rel = Relation.objects.get(id=element_id)
        if rel:
            if 'type' in kwargs:
                if rel.type != kwargs['type']:
                    # check this new relation type not already exists
                    if Relation.objects.filter(type=kwargs['type'], object_id=rel.object_id,
                                              content_type__pk=rel.content_type.id).count()> 0:
                        raise ValidationError( 'Relation type:%s already exists.' % kwargs['type'])
                    else:
                        rel.type = kwargs['type']

            if 'value' in kwargs:
                rel.value = kwargs['value']
            rel.save()
        else:
            raise ObjectDoesNotExist("No relation element exists for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        rel = Relation.objects.get(id=element_id)
        if rel:
            rel.delete()
        else:
            raise ObjectDoesNotExist("No relation element exists for id:%d." % element_id)

class Identifier(AbstractMetaDataElement):
    term = 'Identifier'
    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            # check the identifier name doesn't already exist - identifier name needs to be unique per resource
            idf = Identifier.objects.filter(name__iexact= kwargs['name'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if idf:
                raise ValidationError('Identifier name:%s already exists' % kwargs['name'])
            if kwargs['name'].lower() == 'doi':
                if not metadata_obj.resource.doi:
                    raise ValidationError("Identifier of 'DOI' type can't be created for a resource that has not been assign a DOI yet.")

            if 'url' in kwargs:
                idf = Identifier.objects.create(name=kwargs['name'], url=kwargs['url'], content_object=metadata_obj)
                return idf
            else:
                raise ValidationError('URL for the identifier is missing.')

        else:
            raise ValidationError("Name of identifier element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        idf = Identifier.objects.get(id=element_id)
        if idf:
            if 'name' in kwargs:
                if idf.name.lower() != kwargs['name'].lower():
                    if idf.name.lower() == 'hydroshareidentifier':
                        if not 'migration' in kwargs:
                            raise ValidationError("Identifier name 'hydroshareIdentifier' can't be changed.")

                    if idf.name.lower() == 'doi':
                        raise ValidationError("Identifier name 'DOI' can't be changed.")

                    # check this new identifier name not already exists
                    if Identifier.objects.filter(name__iexact=kwargs['name'], object_id=idf.object_id,
                                              content_type__pk=idf.content_type.id).count()> 0:
                        if not 'migration' in kwargs:
                            raise ValidationError('Identifier name:%s already exists.' % kwargs['name'])

                    idf.name = kwargs['name']

            if 'url' in kwargs:
                if idf.url.lower() != kwargs['url'].lower():
                    if idf.name.lower() == 'hydroshareidentifier':
                        if not 'migration' in kwargs:
                            raise  ValidationError("Hydroshare identifier url value can't be changed.")

                    # if idf.url.lower().find('http://hydroshare.org/resource') == 0:
                    #     raise  ValidationError("Hydroshare identifier url value can't be changed.")
                    # check this new identifier name not already exists
                    if Identifier.objects.filter(url__iexact=kwargs['url'], object_id=idf.object_id,
                                                 content_type__pk=idf.content_type.id).count()> 0:
                        raise ValidationError('Identifier URL:%s already exists.' % kwargs['url'])

                    idf.url = kwargs['url']

            idf.save()
        else:
            raise ObjectDoesNotExist( "No identifier element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        idf = Identifier.objects.get(id=element_id)
        if idf:
            if idf.name.lower() == 'hydroshareidentifier':
                raise ValidationError("Hydroshare identifier:%s can't be deleted." % idf.name)

            if idf.name.lower() == 'doi':
                if idf.content_object.resource.doi:
                    raise ValidationError("Hydroshare identifier:%s can't be deleted for a resource that has been assigned a DOI." % idf.name)
            idf.delete()
        else:
            raise ObjectDoesNotExist("No identifier element was found for id:%d." % element_id)


class Publisher(AbstractMetaDataElement):
    term = 'Publisher'
    name = models.CharField(max_length=200)
    url = models.URLField()

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            metadata_obj = kwargs['content_object']
            if 'url' in kwargs:
                if not metadata_obj.resource.public and metadata_obj.resource.published_and_frozen:
                    raise ValidationError("Publisher element can't be created for a resource that is not shared nor published.")
                if kwargs['name'].lower() == 'hydroshare':
                    if not  metadata_obj.resource.files.all():
                        raise ValidationError("Hydroshare can't be the publisher for a resource that has no content files.")
                    else:
                        kwargs['name'] = 'HydroShare'
                        kwargs['url'] = 'http://hydroshare.org'
                return Publisher.objects.create(name=kwargs['name'], url=kwargs['url'], content_object=metadata_obj)
            else:
                raise ValidationError('URL for the publisher is missing.')
        else:
            raise ValidationError("Name of publisher is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        pub = Publisher.objects.get(id=element_id)
        metadata_obj = kwargs['content_object']

        if metadata_obj.resource.frozen:
            raise ValidationError("Resource metadata can't be edited when the resource is in frozen state.")

        if metadata_obj.resource.published_and_frozen:
            raise ValidationError("Resource metadata can't be edited once the resource has been published.")

        if pub:
            if 'name' in kwargs:
                if pub.name.lower() != kwargs['name'].lower():
                    if pub.name.lower() == 'hydroshare':
                        if metadata_obj.resource.files.all():
                            raise ValidationError("Publisher 'HydroShare' can't be changed for a resource that has content files.")
                    elif kwargs['name'].lower() == 'hydroshare':
                        if not metadata_obj.resource.files.all():
                            raise ValidationError("'HydroShare' can't be a publisher for a resource that has no content files.")

                    if metadata_obj.resource.files.all():
                        pub.name = 'HydroShare'
                    else:
                        pub.name = kwargs['name']

            if 'url' in kwargs:
                if pub.url != kwargs['url']:
                    # make sure we are not changing the url for hydroshare publisher
                    if pub.name.lower() == 'hydroshare':
                        pub.url = 'http://hydroshare.org'
                    else:
                        pub.url = kwargs['url']
            pub.save()
        else:
            raise ObjectDoesNotExist("No publisher element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        pub = Publisher.objects.get(id=element_id)

        if pub.content_object.resource.frozen:
            raise ValidationError("Resource metadata can't be edited when the resource is in frozen state.")

        if pub.content_object.resource.published_and_frozen:
            raise ValidationError("Resource metadata can't be edited once the resource has been published.")

        if pub.content_object.resource.public:
            raise ValidationError("Resource publisher can't be deleted for shared resource.")

        if pub:
            if pub.name.lower() == 'hydroshare':
                if pub.content_object.resource.files.all():
                    raise ValidationError("Publisher HydroShare can't be deleted for a resource that has content files.")
            if pub.content_object.resource.public:
                raise ValidationError("Publisher can't be deleted for a public resource.")
            pub.delete()
        else:
            raise ObjectDoesNotExist("No publisher element was found for id:%d." % element_id)

class Language(AbstractMetaDataElement):
    term = 'Language'
    code = models.CharField(max_length=3, choices=iso_languages )

    def __unicode__(self):
        return self.code

    @classmethod
    def create(cls, **kwargs):
        if 'code' in kwargs:
            # check the code doesn't already exists - format values need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            lang = Language.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).first()
            if lang:
                raise ValidationError('Language element already exists.')

            # check the code is a valid code
            if not [t for t in iso_languages if t[0]==kwargs['code']]:
                raise ValidationError('Invalid language code:%s' % kwargs['code'])

            lang = Language.objects.create(code=kwargs['code'], content_object=metadata_obj)
            return lang
        else:
            raise ValidationError("Language code is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        lang = Language.objects.get(id=element_id)
        if lang:
            if 'code' in kwargs:
                # validate code
                if not [t for t in iso_languages if t[0]==kwargs['code']]:
                    raise ValidationError('Invalid language code:%s' % kwargs['code'])

                if lang.code != kwargs['code']:
                    # check this new language not already exists
                    if Language.objects.filter(code=kwargs['code'], object_id=lang.object_id,
                                             content_type__pk=lang.content_type.id).count()> 0:
                        raise ValidationError('Language:%s already exists.' % kwargs['code'])

                lang.code = kwargs['code']
                lang.save()
            else:
                raise ValidationError('Language code is missing.')
        else:
            raise ObjectDoesNotExist("No language element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        lang = Language.objects.get(id=element_id)
        if lang:
            lang.delete()
        else:
            raise ObjectDoesNotExist("No language element was found for id:%d." % element_id)

class Coverage(AbstractMetaDataElement):
    COVERAGE_TYPES = (
        ('box', 'Box'),
        ('point', 'Point'),
        ('period', 'Period')
    )

    term = 'Coverage'
    type = models.CharField(max_length=20, choices=COVERAGE_TYPES)
    """
    _value field stores a json string. The content of the json
     string depends on the type of coverage as shown below. All keys shown in json string are required.

     For coverage type: period
         _value = "{'name':coverage name value here (optional), 'start':start date value, 'end':end date value, 'scheme':'W3C-DTF}"

     For coverage type: point
         _value = "{'east':east coordinate value,
                    'north':north coordinate value,
                    'units:units applying to (east. north),
                    'name':coverage name value here (optional),
                    'elevation': coordinate in the vertical direction (optional),
                    'zunits': units for elevation (optional),
                    'projection': name of the projection (optional),
                    }"

     For coverage type: box
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                    'units:units applying to 4 limits (north, east, south & east),
                    'name':coverage name value here (optional),
                    'uplimit':uppermost coordinate value (optional),
                    'downlimit':lowermost coordinate value (optional),
                    'zunits': units for uplimit/downlimit (optional),
                    'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024)

    @property
    def value(self):
        print self._value
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        # TODO: validate coordinate values
        if 'type' in kwargs:
            # check the type doesn't already exists - we allow only one coverage type per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            coverage = Coverage.objects.filter(type= kwargs['type'], object_id=metadata_obj.id,
                                               content_type=metadata_type).first()
            if coverage:
                raise ValidationError('Coverage type:%s already exists' % kwargs['type'])

            if not kwargs['type'] in ['box', 'point', 'period']:
                raise ValidationError('Invalid coverage type:%s' % kwargs['type'])

            if kwargs['type'] == 'box':
                # check that there is not already a coverage of point type
                coverage = Coverage.objects.filter(type= 'point', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Box' can't be created when there is a coverage of type 'Point'")
            elif kwargs['type'] == 'point':
                # check that there is not already a coverage of box type
                coverage = Coverage.objects.filter(type= 'box', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Point' can't be created when there is a coverage of type 'Box'")

            if 'value' in kwargs:
                if isinstance(kwargs['value'], dict):
                    # if not 'name' in kwargs['value']:
                    #     raise ValidationError("Coverage name attribute is missing.")

                    cls._validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])

                    if kwargs['type'] == 'period':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems() if k in ('name', 'start', 'end')}
                    elif kwargs['type']== 'point':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems()
                                      if k in ('name', 'east', 'north', 'units', 'elevation', 'zunits', 'projection')}
                    elif kwargs['type']== 'box':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems()
                                      if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'name',
                                               'uplimit', 'downlimit', 'zunits', 'projection')}

                    value_json = json.dumps(value_dict)
                    cov = Coverage.objects.create(type=kwargs['type'], _value=value_json,
                                                  content_object=metadata_obj)
                    return cov
                else:
                    raise ValidationError('Invalid coverage value format.')
            else:
                raise ValidationError('Coverage value is missing.')

        else:
            raise ValidationError("Type of coverage element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        # TODO: validate coordinate values
        cov = Coverage.objects.get(id=element_id)
        changing_coverage_type = False
        if cov:
            if 'type' in kwargs:
                if cov.type != kwargs['type']:
                    # check this new coverage type not already exists
                    if Coverage.objects.filter(type=kwargs['type'], object_id=cov.object_id,
                                               content_type__pk=cov.content_type.id).count()> 0:
                        raise ValidationError('Coverage type:%s already exists.' % kwargs['type'])
                    else:
                        if 'value' in kwargs:
                            if isinstance(kwargs['value'], dict):
                                cls._validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])
                            else:
                                raise ValidationError('Invalid coverage value format.')
                        else:
                            raise ValidationError('Coverage value is missing.')

                        changing_coverage_type = True

            if 'value' in kwargs:
                if not isinstance(kwargs['value'], dict):
                    raise ValidationError('Invalid coverage value format.')

                if changing_coverage_type:
                    value_dict = {}
                    cov.type = kwargs['type']
                else:
                    value_dict = cov.value

                if 'name' in kwargs['value']:
                    value_dict['name'] = kwargs['value']['name']

                if cov.type == 'period':
                    for item_name in ('start', 'end'):
                        if item_name in kwargs['value']:
                            value_dict[item_name] = kwargs['value'][item_name]
                elif cov.type == 'point':
                    for item_name in ('east', 'north', 'units', 'elevation', 'zunits', 'projection'):
                        if item_name in kwargs['value']:
                            value_dict[item_name] = kwargs['value'][item_name]
                elif cov.type == 'box':
                    for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'uplimit',
                                      'downlimit', 'zunits', 'projection'):
                        if item_name in kwargs['value']:
                            value_dict[item_name] = kwargs['value'][item_name]

                value_json = json.dumps(value_dict)
                cov._value = value_json
            cov.save()
        else:
            raise ObjectDoesNotExist("No coverage element was found for the provided id:%s" % element_id)


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Coverage element can't be deleted.")

    @classmethod
    def _validate_coverage_type_value_attributes(cls, coverage_type, value_dict):
        if coverage_type == 'period':
            # check that all the required sub-elements exist
            if not 'start' in value_dict or not 'end' in value_dict:
                raise ValidationError("For coverage of type 'period' values for both start date and end date are needed.")
            else:
                # validate the date values
                try:
                    start_dt = parser.parse(value_dict['start'])
                except TypeError:
                    raise TypeError("Invalid start date. Not a valid date value.")
                try:
                    end_dt = parser.parse(value_dict['end'])
                except TypeError:
                    raise TypeError("Invalid end date. Not a valid date value.")
        elif coverage_type == 'point':
            # check that all the required sub-elements exist
            if not 'east' in value_dict or not 'north' in value_dict or not 'units' in value_dict:
                raise ValidationError("For coverage of type 'point' values for 'east', 'north' and 'units' are needed.")
        elif coverage_type == 'box':
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if not value_item in value_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more bounding box limits or 'units' is missing.")

class Format(AbstractMetaDataElement):
    term = 'Format'
    value = models.CharField(max_length=150)

    def __unicode__(self):
        return self.value

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            # check the format doesn't already exists - format values need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            format = Format.objects.filter(value__iexact= kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if format:
                raise ValidationError('Format:%s already exists' % kwargs['value'])

            return Format.objects.create(**kwargs)

        else:
            raise ValidationError("Format value is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        format = Format.objects.get(id=element_id)
        if format:
            if 'value' in kwargs:
                if format.value != kwargs['value']:
                    # check this new format not already exists
                    if Format.objects.filter(value=kwargs['value'], object_id=format.object_id,
                                             content_type__pk=format.content_type.id).count()> 0:
                        raise ValidationError('Format:%s already exists.' % kwargs['value'])

                format.value = kwargs['value']
                format.save()
            else:
                raise ValidationError('Value for format is missing.')
        else:
            raise ObjectDoesNotExist("No format element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        format = Format.objects.get(id=element_id)
        if format:
            format.delete()
        else:
            raise ObjectDoesNotExist("No format element was found for id:%d." % element_id)

class Subject(AbstractMetaDataElement):
    term = 'Subject'
    value = models.CharField(max_length=100)

    def __unicode__(self):
        return self.value

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            # check the subject doesn't already exists - subjects need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            sub = Subject.objects.filter(value__iexact=kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if sub:
                raise ValidationError('Subject:%s already exists for this resource.' % kwargs['value'])

            return Subject.objects.create(**kwargs)

        else:
            raise ValidationError("Subject value is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        sub = Subject.objects.get(id=element_id)
        if sub:
            if 'value' in kwargs:
                if sub.value != kwargs['value']:
                    # check this new subject not already exists
                    if Subject.objects.filter(value__iexact=kwargs['value'], object_id=sub.object_id,
                                             content_type__pk=sub.content_type.id).count() > 0:
                        raise ValidationError('Subject:%s already exists for this resource.' % kwargs['value'])

                sub.value = kwargs['value']
                sub.save()
            else:
                raise ValidationError('Value for subject is missing.')
        else:
            raise ObjectDoesNotExist("No format element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        sub = Subject.objects.get(id=element_id)
        if sub:
            if Subject.objects.filter(object_id=sub.object_id,
                                      content_type__pk=sub.content_type.id).count() == 1:
                raise ValidationError("The only subject element of the resource con't be deleted.")
            sub.delete()
        else:
            raise ObjectDoesNotExist("No subject element was found for id:%d." % element_id)

class Source(AbstractMetaDataElement):
    term = 'Source'
    derived_from = models.CharField(max_length=300)

    def __unicode__(self):
        return self.derived_from

    @classmethod
    def create(cls, **kwargs):
        if 'derived_from' in kwargs:
            # check the source doesn't already exists - source needs to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            src = Source.objects.filter(derived_from=kwargs['derived_from'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if src:
                raise ValidationError('Source:%s already exists for this resource.' % kwargs['derived_from'])

            return Source.objects.create(**kwargs)

        else:
            raise ValidationError("Source data is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        src = Source.objects.get(id=element_id)
        if src:
            if 'derived_from' in kwargs:
                if src.derived_from != kwargs['derived_from']:
                    # check this new derived_from not already exists
                    if Source.objects.filter(derived_from__iexact=kwargs['derived_from'], object_id=src.object_id,
                                              content_type__pk=src.content_type.id).count()> 0:
                        raise ValidationError('Source:%s already exists for this resource.' % kwargs['value'])

                src.derived_from = kwargs['derived_from']
                src.save()
            else:
                raise ValidationError('Value for source is missing.')
        else:
            raise ObjectDoesNotExist("No source element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        src = Source.objects.get(id=element_id)
        if src:
            src.delete()
        else:
            raise ObjectDoesNotExist("No source element was found for id:%d." % element_id)

class Rights(AbstractMetaDataElement):
    term = 'Rights'
    statement = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        # the Meta class setting "unique-tigether' enforces that we have only one rights element per resource
        metadata_obj = kwargs['content_object']

        # in order to create a Rights element we need to have either a value for the statement field or a value for the url field
        if 'statement' in kwargs and 'url' in kwargs:
            return Rights.objects.create(statement=kwargs['statement'], url=kwargs['url'],  content_object=metadata_obj)

        elif 'url' in kwargs:
            return Rights.objects.create(url=kwargs['url'],  content_object=metadata_obj)

        elif 'statement' in kwargs:
            return Rights.objects.create(statement=kwargs['statement'],  content_object=metadata_obj)

        else:
            raise ValidationError("Statement and/or URL of rights is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        rights = Rights.objects.get(id=element_id)
        if rights:
            if 'statement' in kwargs:
                rights.statement = kwargs['statement']
            if 'url' in kwargs:
                rights.url = kwargs['url']
            rights.save()
        else:
            raise ObjectDoesNotExist("No rights element was found for the provided id:%s" % element_id)


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Rights element of a resource can't be deleted.")



def short_id():
    return uuid4().hex

class AbstractResource(ResourcePermissionsMixin):
    """
    All hydroshare objects inherit from this mixin.  It defines things that must
    be present to be considered a hydroshare resource.  Additionally, all
    hydroshare resources should inherit from Page.  This gives them what they
    need to be represented in the Mezzanine CMS.

    In some cases, it is possible that the order of inheritence matters.  Best
    practice dictates that you list pages.Page first and then other classes:

        class MyResourceContentType(pages.Page, hs_core.AbstractResource):
            ...
    """
    content = models.TextField() # the field added for use by Django inplace editing
    last_changed_by = models.ForeignKey(User,
                                        help_text='The person who last changed the resource',
                                        related_name='last_changed_%(app_label)s_%(class)s',
                                        null=True
    )

    # dublin_metadata = generic.GenericRelation(
    #     'dublincore.QualifiedDublinCoreElement',
    #     help_text='The dublin core metadata of the resource'
    # )

    files = generic.GenericRelation('hs_core.ResourceFile', help_text='The files associated with this resource')
    bags = generic.GenericRelation('hs_core.Bags', help_text='The bagits created from versions of this resource')
    short_id = models.CharField(max_length=32, default=short_id, db_index=True)
    doi = models.CharField(max_length=1024, blank=True, null=True, db_index=True,
                           help_text='Permanent identifier. Never changes once it\'s been set.')
    comments = CommentsField()
    rating = RatingField()

    # this is to establish a relationship between a resource and
    # any metadata container object (e.g., CoreMetaData object)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    @classmethod
    def bag_url(cls, resource_id):
        bagit_path = getattr(settings, 'IRODS_BAGIT_PATH', 'bags')
        bagit_postfix = getattr(settings, 'IRODS_BAGIT_POSTFIX', 'zip')

        bag_path = "{path}/{resource_id}.{postfix}".format(path=bagit_path,
                                                           resource_id=resource_id,
                                                           postfix=bagit_postfix)
        istorage = IrodsStorage()
        bag_url = istorage.url(bag_path)

        return bag_url

    def delete(self, using=None):
        from hydroshare import hs_bagit

        for fl in self.files.all():
            fl.resource_file.delete()

        hs_bagit.delete_bag(self)

        self.metadata.delete_all_elements()
        self.metadata.delete()

        access_resource = self.raccess
        UserResourcePrivilege.objects.filter(resource=access_resource).delete()
        GroupResourcePrivilege.objects.filter(resource=access_resource).delete()
        access_resource.delete()

        super(AbstractResource, self).delete()

    # this property needs to be overriden by any specific resource type
    # that needs additional metadata elements on top of core metadata data elements
    @property
    def metadata(self):
        md = CoreMetaData() # only this line needs to be changed when you override
        return self._get_metadata(md)

    @property
    def first_creator(self):
        first_creator = self.metadata.creators.filter(order=1).first()
        return first_creator

    def _get_metadata(self, metatdata_obj):
        md_type = ContentType.objects.get_for_model(metatdata_obj)
        res_type = ContentType.objects.get_for_model(self)
        self.content_object = res_type.model_class().objects.get(id=self.id).content_object
        if self.content_object:
            return self.content_object
        else:
            metatdata_obj.save()
            self.content_type = md_type
            self.object_id = metatdata_obj.id
            self.save()
            return metatdata_obj

    def extra_capabilites(self):
        """This is not terribly well defined yet, but should return at the least a JSON serializable object of URL
        endpoints where extra self-describing services exist and can be queried by the user in the form of
        { "name" : "endpoint" }
        """
        return None

    def get_citation(self):
        citation = ''

        CREATOR_NAME_ERROR = "Failed to generate citation - invalid creator name."
        CITATION_ERROR = "Failed to generate citation."

        first_author = self.metadata.creators.all().filter(order=1)[0]
        name_parts = first_author.name.split()
        if len(name_parts) == 0:
            citation = CREATOR_NAME_ERROR
            return citation

        if len(name_parts) > 2:
            citation = "{last_name}, {first_initial}.{middle_initial}.".format(last_name=name_parts[-1],
                                                                              first_initial=name_parts[0][0],
                                                                              middle_initial=name_parts[1][0]) + ", "
        else:
            citation = "{last_name}, {first_initial}.".format(last_name=name_parts[-1],
                                                              first_initial=name_parts[0][0]) + ", "

        other_authors = self.metadata.creators.all().filter(order__gt=1)
        for author in other_authors:
            name_parts = author.name.split()
            if len(name_parts) == 0:
                citation = CREATOR_NAME_ERROR
                return citation

            if len(name_parts) > 2:
                citation += "{first_initial}.{middle_initial}.{last_name}".format(first_initial=name_parts[0][0],
                                                                                  middle_initial=name_parts[1][0],
                                                                                  last_name=name_parts[-1]) + ", "
            else:
                citation += "{first_initial}.{last_name}".format(first_initial=name_parts[0][0],
                                                                 last_name=name_parts[-1]) + ", "

        #  remove the last added comma and the space
        if len(citation) > 2:
            citation = citation[:-2]
        else:
            return CITATION_ERROR

        if self.metadata.dates.all().filter(type='published'):
            citation_date = self.metadata.dates.all().filter(type='published')[0]
        elif self.metadata.dates.all().filter(type='modified'):
            citation_date = self.metadata.dates.all().filter(type='modified')[0]
        else:
            return CITATION_ERROR

        citation += " ({year}). ".format(year=citation_date.start_date.year)
        citation += self.title
        citation += ", HydroShare, "

        if self.metadata.identifiers.all().filter(name="doi"):
            hs_identifier = self.metadata.identifiers.all().filter(name="doi")[0]
        elif self.metadata.identifiers.all().filter(name="hydroShareIdentifier"):
            hs_identifier = self.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        else:
            return CITATION_ERROR

        citation += "{url}".format(url=hs_identifier.url)

        return citation

    @property
    def can_be_public(self):
        if self.metadata.has_all_required_elements():
            return True

        return False

    @classmethod
    def get_supported_upload_file_types(cls):
        # NOTES FOR ANY SUBCLASS OF THIS CLASS TO OVERRIDE THIS FUNCTION:
        # to allow only specific file types return a tuple of those file extensions (ex: return (".csv", ".txt",))
        # to not allow any file upload, return a empty tuple ( return ())

        # by default all file types are supported
        return (".*",)


    @classmethod
    def can_have_multiple_files(cls):
        # NOTES FOR ANY SUBCLASS OF THIS CLASS TO OVERRIDE THIS FUNCTION:
        # to allow resource to have only 1 file or no file, return False

        # resource by default can have multiple files
        return True


    class Meta:
        abstract = True
        unique_together = ("content_type", "object_id")

def get_path(instance, filename):
    return os.path.join(instance.content_object.short_id, 'data', 'contents', filename)

class ResourceFile(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id')
    resource_file = models.FileField(upload_to=get_path, max_length=500, storage=IrodsStorage() if getattr(settings,'USE_IRODS', False) else DefaultStorage())

class Bags(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id')
    timestamp = models.DateTimeField(default=now, db_index=True)

    class Meta:
        ordering = ['-timestamp']


# remove RichText parent class from the parameters for Django inplace editing to work; otherwise, get internal edit error when saving changes
class GenericResource(Page, AbstractResource):

    class Meta:
        verbose_name = 'Generic'

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)


    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

    @classmethod
    def can_have_multiple_files(cls):
        return True

    @classmethod
    def can_have_files(cls):
        return True

# This model has a one-to-one relation with the AbstractResource model
class CoreMetaData(models.Model):
    #from django.contrib.sites.models import Site
    #_domain = 'hydroshare.org'  #Site.objects.get_current() # this one giving error since the database does not have a related table called 'django_site'

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf':"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms':"http://purl.org/dc/terms/",
                  'hsterms': "http://hydroshare.org/terms/"}

    id = models.AutoField(primary_key=True)

    _description = generic.GenericRelation(Description)    # resource abstract
    _title = generic.GenericRelation(Title)
    creators = generic.GenericRelation(Creator)
    contributors = generic.GenericRelation(Contributor)
    dates = generic.GenericRelation(Date)
    coverages = generic.GenericRelation(Coverage)
    formats = generic.GenericRelation(Format)
    identifiers = generic.GenericRelation(Identifier)
    _language = generic.GenericRelation(Language)
    subjects = generic.GenericRelation(Subject)
    sources = generic.GenericRelation(Source)
    relations = generic.GenericRelation(Relation)
    _rights = generic.GenericRelation(Rights)
    _type = generic.GenericRelation(Type)
    _publisher = generic.GenericRelation(Publisher)

    @property
    def title(self):
        return self._title.all().first()

    @property
    def description(self):
        return self._description.all().first()

    @property
    def language(self):
        return self._language.all().first()

    @property
    def rights(self):
        return self._rights.all().first()

    @property
    def type(self):
        return self._type.all().first()

    @property
    def publisher(self):
        return self._publisher.all().first()

    @classmethod
    def get_supported_element_names(cls):
        return ['Description',
                'Creator',
                'Contributor',
                'Coverage',
                'Format',
                'Rights',
                'Title',
                'Type',
                'Date',
                'Identifier',
                'Language',
                'Subject',
                'Source',
                'Relation',
                'Publisher']

    # this method needs to be overriden by any subclass of this class
    # if they implement additional metadata elements that are required
    def has_all_required_elements(self):
        if not self.title:
            return False
        elif self.title.value.lower() == 'untitled resource':
            return False

        if not self.description:
            return False
        elif len(self.description.abstract.strip()) == 0:
            return False

        if self.creators.count() == 0:
            return False

        if not self.rights:
            return False
        elif len(self.rights.statement.strip()) == 0:
            return False

        # if self.coverages.count() == 0:
        #     return False

        if self.subjects.count() == 0:
            return False

        return True

    # this method needs to be overriden by any subclass of this class
    # if they implement additional metadata elements that are required
    def get_required_missing_elements(self):
        missing_required_elements = []

        if not self.title:
            missing_required_elements.append('Title')
        if not self.description:
            missing_required_elements.append('Abstract')
        if not self.rights:
            missing_required_elements.append('Rights')
        if self.subjects.count() == 0:
            missing_required_elements.append('Keywords')

        return missing_required_elements

    # this method needs to be overriden by any subclass of this class
    def delete_all_elements(self):
        if self.title: self.title.delete()
        if self.description: self.description.delete()
        if self.language: self.language.delete()
        if self.rights: self.rights.delete()
        if self.publisher: self.publisher.delete()
        if self.type: self.type.delete()

        self.creators.all().delete()
        self.contributors.all().delete()
        self.dates.all().delete()
        self.identifiers.all().delete()
        self.coverages.all().delete()
        self.formats.all().delete()
        self.subjects.all().delete()
        self.sources.all().delete()
        self.relations.all().delete()

    def get_xml(self, pretty_print=True):
        from lxml import etree

        RDF_ROOT = etree.Element('{%s}RDF' % self.NAMESPACES['rdf'], nsmap=self.NAMESPACES)
        # create the Description element -this is not exactly a dc element
        rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % self.NAMESPACES['rdf'])

        #resource_uri = self.HYDROSHARE_URL + '/resource/' + self.resource.short_id
        resource_uri = self.identifiers.all().filter(name='hydroShareIdentifier')[0].url
        rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], resource_uri)

        # create the title element
        if self.title:
            dc_title = etree.SubElement(rdf_Description, '{%s}title' % self.NAMESPACES['dc'])
            dc_title.text = self.title.value

        # create the type element
        if self.type:
            dc_type = etree.SubElement(rdf_Description, '{%s}type' % self.NAMESPACES['dc'])
            dc_type.set('{%s}resource' % self.NAMESPACES['rdf'], self.type.url)

        # create the Description element (we named it as Abstract to differentiate from the parent "Description" element)
        if self.description:
            dc_description = etree.SubElement(rdf_Description, '{%s}description' % self.NAMESPACES['dc'])
            dc_des_rdf_Desciption = etree.SubElement(dc_description, '{%s}Description' % self.NAMESPACES['rdf'])
            dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption, '{%s}abstract' % self.NAMESPACES['dcterms'])
            dcterms_abstract.text = self.description.abstract

        # use all creators associated with this metadata object to
        # generate creator xml elements
        for creator in self.creators.all():
            self._create_person_element(etree, rdf_Description, creator)

        for contributor in self.contributors.all():
            self._create_person_element(etree, rdf_Description, contributor)

        for coverage in self.coverages.all():
            dc_coverage = etree.SubElement(rdf_Description, '{%s}coverage' % self.NAMESPACES['dc'])
            cov_dcterm = '{%s}' + coverage.type
            dc_coverage_dcterms = etree.SubElement(dc_coverage, cov_dcterm % self.NAMESPACES['dcterms'])
            rdf_coverage_value = etree.SubElement(dc_coverage_dcterms, '{%s}value' % self.NAMESPACES['rdf'])
            if coverage.type == 'period':
                start_date = parser.parse(coverage.value['start'])
                end_date = parser.parse(coverage.value['end'])
                cov_value = 'start=%s; end=%s; scheme=W3C-DTF' % (start_date.isoformat(), end_date.isoformat())

                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value

            elif coverage.type == 'point':
                cov_value = 'east=%s; north=%s; units=%s' % (coverage.value['east'], coverage.value['north'],
                                                  coverage.value['units'])
                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value
                if 'elevation' in coverage.value:
                    cov_value = cov_value + '; elevation=%s' % coverage.value['elevation']
                    if 'zunits' in coverage.value:
                        cov_value = cov_value + '; zunits=%s' % coverage.value['zunits']
                if 'projection' in coverage.value:
                    cov_value = cov_value + '; projection=%s' % coverage.value['projection']

            else: # this is box type
                cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                            %(coverage.value['northlimit'], coverage.value['eastlimit'],
                              coverage.value['southlimit'], coverage.value['westlimit'], coverage.value['units'])

                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value
                if 'uplimit' in coverage.value:
                    cov_value = cov_value + '; uplimit=%s' % coverage.value['uplimit']
                if 'downlimit' in coverage.value:
                    cov_value = cov_value + '; downlimit=%s' % coverage.value['downlimit']
                if 'uplimit' in coverage.value or 'downlimit' in coverage.value:
                    cov_value = cov_value + '; zunits=%s' % coverage.value['zunits']
                if 'projection' in coverage.value:
                    cov_value = cov_value + '; projection=%s' % coverage.value['projection']

            rdf_coverage_value.text = cov_value

        for dt in self.dates.all():
            dc_date = etree.SubElement(rdf_Description, '{%s}date' % self.NAMESPACES['dc'])
            dc_term = '{%s}'+ dt.type
            dc_date_dcterms = etree.SubElement(dc_date, dc_term % self.NAMESPACES['dcterms'])
            rdf_date_value = etree.SubElement(dc_date_dcterms, '{%s}value' % self.NAMESPACES['rdf'])
            if dt.type != 'valid':
                rdf_date_value.text = dt.start_date.isoformat()
            else:
                if dt.end_date:
                    rdf_date_value.text = "start=%s; end=%s" % (dt.start_date.isoformat(), dt.end_date.isoformat())
                else:
                    rdf_date_value.text = dt.start_date.isoformat()

        for fmt in self.formats.all():
            dc_format = etree.SubElement(rdf_Description, '{%s}format' % self.NAMESPACES['dc'])
            dc_format.text = fmt.value

        for res_id in self.identifiers.all():
            dc_identifier = etree.SubElement(rdf_Description, '{%s}identifier' % self.NAMESPACES['dc'])
            dc_id_rdf_Description = etree.SubElement(dc_identifier, '{%s}Description' % self.NAMESPACES['rdf'])
            id_hsterm = '{%s}' + res_id.name
            hsterms_hs_identifier = etree.SubElement(dc_id_rdf_Description, id_hsterm % self.NAMESPACES['hsterms'])
            hsterms_hs_identifier.text = res_id.url

        if self.language:
            dc_lang = etree.SubElement(rdf_Description, '{%s}language' % self.NAMESPACES['dc'])
            dc_lang.text = self.language.code

        if self.publisher:
            dc_publisher = etree.SubElement(rdf_Description, '{%s}publisher' % self.NAMESPACES['dc'])
            dc_pub_rdf_Description = etree.SubElement(dc_publisher, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_pub_name = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherName' % self.NAMESPACES['hsterms'])
            hsterms_pub_name.text = self.publisher.name
            hsterms_pub_url = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherURL' % self.NAMESPACES['hsterms'])
            hsterms_pub_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.publisher.url)

        for rel in self.relations.all():
            dc_relation = etree.SubElement(rdf_Description, '{%s}relation' % self.NAMESPACES['dc'])
            dc_rel_rdf_Description = etree.SubElement(dc_relation, '{%s}Description' % self.NAMESPACES['rdf'])
            rel_dcterm = '{%s}' + rel.type
            dcterms_type = etree.SubElement(dc_rel_rdf_Description, rel_dcterm % self.NAMESPACES['dcterms'])
            # check if the relation value starts with 'http://' or 'https://'
            if rel.value.lower().find('http://') == 0 or rel.value.lower().find('https://') == 0:
                dcterms_type.set('{%s}resource' % self.NAMESPACES['rdf'], rel.value)
            else:
                dcterms_type.text = rel.value

        for src in self.sources.all():
            dc_source = etree.SubElement(rdf_Description, '{%s}source' % self.NAMESPACES['dc'])
            dc_source_rdf_Description = etree.SubElement(dc_source, '{%s}Description' % self.NAMESPACES['rdf'])
            dcterms_derived_from = etree.SubElement(dc_source_rdf_Description, '{%s}isDerivedFrom' % self.NAMESPACES['dcterms'])
            # if the source value starts with 'http://' or 'https://' add value as an attribute
            if src.derived_from.lower().find('http://') == 0 or src.derived_from.lower().find('https://') == 0:
                dcterms_derived_from.set('{%s}resource' % self.NAMESPACES['rdf'], src.derived_from)
            else:
                dcterms_derived_from.text = src.derived_from

        if self.rights:
            dc_rights = etree.SubElement(rdf_Description, '{%s}rights' % self.NAMESPACES['dc'])
            dc_rights_rdf_Description = etree.SubElement(dc_rights, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_statement = etree.SubElement(dc_rights_rdf_Description, '{%s}rightsStatement' % self.NAMESPACES['hsterms'])
            hsterms_statement.text = self.rights.statement
            if self.rights.url:
                hsterms_url = etree.SubElement(dc_rights_rdf_Description, '{%s}URL' % self.NAMESPACES['hsterms'])
                hsterms_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.rights.url)

        for sub in self.subjects.all():
            dc_subject = etree.SubElement(rdf_Description, '{%s}subject' % self.NAMESPACES['dc'])
            if sub.value.lower().find('http://') == 0 or sub.value.lower().find('https://') == 0:
                dc_subject.set('{%s}resource' % self.NAMESPACES['rdf'], sub.value)
            else:
                dc_subject.text = sub.value

        return self.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def add_metadata_element_to_xml(self, root, md_element, md_fields):
        from lxml import etree

        hsterms_newElem = etree.SubElement(root,
                                           "{{{ns}}}{new_element}".format(ns=self.NAMESPACES['hsterms'], new_element=md_element.term))
        hsterms_newElem_rdf_Desc = etree.SubElement(hsterms_newElem,
                                                    "{{{ns}}}Description".format(ns=self.NAMESPACES['rdf']))
        for md_field in md_fields:
            if hasattr(md_element, md_field):
                attr = getattr(md_element, md_field)
                if attr:
                    field = etree.SubElement(hsterms_newElem_rdf_Desc,
                                             "{{{ns}}}{field}".format(ns=self.NAMESPACES['hsterms'],
                                                                  field=md_field))
                    field.text = str(attr)

    def _create_person_element(self, etree, parent_element, person):

        # importing here to avoid circular import problem
        from hydroshare.utils import current_site_url

        if isinstance(person, Creator):
            dc_person = etree.SubElement(parent_element, '{%s}creator' % self.NAMESPACES['dc'])
        else:
            dc_person = etree.SubElement(parent_element, '{%s}contributor' % self.NAMESPACES['dc'])

        dc_person_rdf_Description = etree.SubElement(dc_person, '{%s}Description' % self.NAMESPACES['rdf'])

        hsterms_name = etree.SubElement(dc_person_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
        hsterms_name.text = person.name
        if person.description:
            dc_person_rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], current_site_url() + person.description)

        if isinstance(person, Creator):
            hsterms_creatorOrder = etree.SubElement(dc_person_rdf_Description, '{%s}creatorOrder' % self.NAMESPACES['hsterms'])
            hsterms_creatorOrder.text = str(person.order)

        if person.organization:
            hsterms_organization = etree.SubElement(dc_person_rdf_Description, '{%s}organization' % self.NAMESPACES['hsterms'])
            hsterms_organization.text = person.organization

        if person.email:
            hsterms_email = etree.SubElement(dc_person_rdf_Description, '{%s}email' % self.NAMESPACES['hsterms'])
            hsterms_email.text = person.email

        if person.address:
            hsterms_address = etree.SubElement(dc_person_rdf_Description, '{%s}address' % self.NAMESPACES['hsterms'])
            hsterms_address.text = person.address

        if person.phone:
            hsterms_phone = etree.SubElement(dc_person_rdf_Description, '{%s}phone' % self.NAMESPACES['hsterms'])
            hsterms_phone.set('{%s}resource' % self.NAMESPACES['rdf'], 'tel:' + person.phone)

        if person.homepage:
            hsterms_homepage = etree.SubElement(dc_person_rdf_Description, '{%s}homepage' % self.NAMESPACES['hsterms'])
            hsterms_homepage.set('{%s}resource' % self.NAMESPACES['rdf'], person.homepage)

        for link in person.external_links.all():
            hsterms_link_type = etree.SubElement(dc_person_rdf_Description, '{%s}' % self.NAMESPACES['hsterms'] + link.type)
            hsterms_link_type.set('{%s}resource' % self.NAMESPACES['rdf'], link.url)

    def create_element(self, element_model_name, **kwargs):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the supported in core metadata elements."
                                  % element_model_name)

        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                kwargs['content_object'] = self
                element = model_type.model_class().create(**kwargs)
                element.save()
                return element
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def update_element(self, element_model_name, element_id, **kwargs):
        element_model_name = element_model_name.lower()
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                kwargs['content_object']= self
                model_type.model_class().update(element_id, **kwargs)
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def delete_element(self, element_model_name, element_id):
        element_model_name = element_model_name.lower()
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                model_type.model_class().remove(element_id)
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def _is_valid_element(self, element_name):
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements


def resource_processor(request, page):
    extra = page_permissions_page_processor(request, page)
    return extra


@receiver(post_save)
def resource_creation_signal_handler(sender, instance, created, **kwargs):
    """Create initial dublin core elements"""
    if isinstance(instance, AbstractResource):
        if created:
            pass
            # from hs_core.hydroshare import utils
            # import json
            # instance.metadata.create_element('title', value=instance.title)
            # if instance.content:
            #     instance.metadata.create_element('description', abstract=instance.content)
            # else:
            #     instance.metadata.create_element('description', abstract=instance.description)

            # TODO: With the current VM the get_user_info() method fails. So we can't get the resource uri for
            # the user now.
            # creator_dict = users.get_user_info(instance.creator)
            # instance.metadata.create_element('creator', name=instance.creator.get_full_name(),
            #                                  email=instance.creator.email,
            #                                  description=creator_dict['resource_uri'])

            #instance.metadata.create_element('creator', name=instance.creator.get_full_name(), email=instance.creator.email)

            # TODO: The element 'Type' can't be created as we do not have an URI for specific resource types yet

            # instance.metadata.create_element('date', type='created', start_date=instance.created)
            # instance.metadata.create_element('date', type='modified', start_date=instance.updated)

            # res_json = utils.serialize_science_metadata(instance)
            # res_dict = json.loads(res_json)
            #instance.metadata.create_element('identifier', name='hydroShareIdentifier', url='http://hydroshare.org/resource{0}{1}'.format('/', instance.short_id))
            instance.set_slug('resource{0}{1}'.format('/', instance.short_id))
        else:
            resource_update_signal_handler(sender, instance, created, **kwargs)

    if isinstance(AbstractResource, sender):
        if created:
            instance.dublin_metadata.create(term='T', content=instance.title)
            instance.dublin_metadata.create(term='CR', content=instance.user.username)
            if instance.last_updated_by:
                instance.dublin_metadata.create(term='CN', content=instance.last_updated_by.username)
            instance.dublin_metadata.create(term='DT', content=instance.created)
            if instance.content:
                instance.dublin_metadata.create(term='AB', content=instance.content)
        else:
            resource_update_signal_handler(sender, instance, created, **kwargs)


def resource_update_signal_handler(sender, instance, created, **kwargs):
    """Add dublin core metadata based on the person who just updated the resource. Handle publishing too..."""


# this import statement is necessary in models.py to receive signals
# any hydroshare app that needs to listen to signals from hs_core also needs to
# implement the appropriate signal handlers in receivers.py and then include this import statement
# in the app's models.py as the last line of code
import receivers
