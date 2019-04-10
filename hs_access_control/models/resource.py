from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, \
        UserResourcePrivilege, GroupResourcePrivilege

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

        return User.objects.filter(Q(is_active=True) &
                                   (Q(u2urp__resource=self.resource,
                                      u2urp__privilege__lte=PrivilegeCodes.VIEW) |
                                    Q(u2ugp__group__gaccess__active=True,
                                      u2ugp__group__g2grp__resource=self.resource,
                                      u2ugp__group__g2grp__privilege__lte=PrivilegeCodes.VIEW)))\
                           .distinct()

    @property
    def edit_users(self):
        """
        QuerySet of users with change privileges

        This is a property so that it is a workalike for a prior explicit list.

        If the resource is immutable, an empty QuerySet is returned.
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
        return Group.objects.filter(g2grp__resource=self.resource,
                                    g2grp__privilege__lte=PrivilegeCodes.VIEW, gaccess__active=True)

    @property
    def edit_groups(self):
        """
        QuerySet of groups with edit privileges

        This is a property so that it is a workalike for a prior explicit list.

        If the resource is immutable, an empty QuerySet is returned.
        """
        if self.immutable:
            return Group.objects.none()
        else:
            return Group.objects.filter(g2grp__resource=self.resource,
                                        g2grp__privilege__lte=PrivilegeCodes.CHANGE,
                                        gaccess__active=True)

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
            return []

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

        if this_user.is_superuser:
            return PrivilegeCodes.OWNER

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
        return min(user_priv, group_priv)

    @property
    def sharing_status(self):

        if self.published:
            return "published"
        elif self.public:
            return "public"
        elif self.discoverable:
            return "discoverable"
        else:
            return "private"
