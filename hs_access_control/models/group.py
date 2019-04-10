from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, UserGroupPrivilege

#############################################
# Group access data.
#
# GroupAccess has a one-to-one correspondence with the Group object
# and contains access control flags and methods specific to groups.
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

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(is_active=True,
                                   u2ugp__group=self.group,
                                   u2ugp__privilege=PrivilegeCodes.OWNER)

    @property
    def edit_users(self):
        """
        Return list of users who can add members to a group.

        :return: list of users

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(is_active=True,
                                   u2ugp__group=self.group,
                                   u2ugp__privilege__lte=PrivilegeCodes.CHANGE)

    @property
    def members(self):
        """
        Return list of members for a group.

        :return: list of users

        This eliminates duplicates due to multiple invitations.
        """

        return User.objects.filter(is_active=True,
                                   u2ugp__group=self.group,
                                   u2ugp__privilege__lte=PrivilegeCodes.VIEW)

    @property
    def view_resources(self):
        """
        QuerySet of resources held by group.

        :return: QuerySet of resource objects held by group.
        """
        return BaseResource.objects.filter(r2grp__group=self.group)

    @property
    def edit_resources(self):
        """
        QuerySet of resources that can be edited by group.

        :return: List of resource objects that can be edited  by this group.
        """
        return BaseResource.objects.filter(r2grp__group=self.group, raccess__immutable=False,
                                           r2grp__privilege__lte=PrivilegeCodes.CHANGE)

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
            return BaseResource.objects.filter(r2grp__privilege=this_privilege,
                                               r2grp__group=self.group)\
                                       .exclude(pk__in=BaseResource.objects
                                                .filter(r2grp__group=self.group,
                                                        r2grp__privilege__lt=this_privilege))

        elif this_privilege == PrivilegeCodes.CHANGE:
            # CHANGE does not include immutable resources
            return BaseResource.objects.filter(raccess__immutable=False,
                                               r2grp__privilege=this_privilege,
                                               r2grp__group=self.group)\
                                       .exclude(pk__in=BaseResource.objects
                                                .filter(r2grp__group=self.group,
                                                        r2grp__privilege__lt=this_privilege))

        else:  # this_privilege == PrivilegeCodes.ViEW
            # VIEW includes CHANGE & immutable as well as explicit VIEW
            view = BaseResource.objects.filter(r2grp__privilege=this_privilege,
                                               r2grp__group=self.group)\
                .exclude(pk__in=BaseResource.objects.filter(r2grp__group=self.group,
                                                            r2grp__privilege__lt=this_privilege))

            immutable = BaseResource.objects.filter(raccess__immutable=True,
                                                    r2grp__privilege=PrivilegeCodes.CHANGE,
                                                    r2grp__group=self.group)\
                                            .exclude(pk__in=BaseResource.objects.filter(
                                                raccess__immutable=True,
                                                r2grp__group=self.group,
                                                r2grp__privilege__lt=PrivilegeCodes.CHANGE))

            return BaseResource.objects.filter(Q(pk__in=view) | Q(pk__in=immutable)).distinct()

    def get_users_with_explicit_access(self, this_privilege):
        """
            Get a list of users for which the group has the specified privilege

            :param this_privilege: one of the PrivilegeCodes
            :return: QuerySet of user objects (QuerySet)
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
        """

        if not this_user.is_active:
            return PrivilegeCodes.NONE
        try:
            p = UserGroupPrivilege.objects.get(group=self.group,
                                               user=this_user)
            return p.privilege
        except UserGroupPrivilege.DoesNotExist:
            return PrivilegeCodes.NONE
