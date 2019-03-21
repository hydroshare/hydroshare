from django.contrib.auth.models import User, Group
from django.db import models
from hs_core.models import BaseResource
from django.db.models import Q, F

###################################
# Communities of groups
###################################


class Community(models.Model):
    """ a placeholder class for a community of groups """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    purpose = models.TextField(null=True, blank=True)
    auto_approve = models.BooleanField(null=False, default=False, blank=False, editable=False)
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    picture = models.ImageField(upload_to='community', null=True, blank=True)

    @property
    def member_groups(self):
        return Group.objects.filter(gaccess__active=True, g2gcp__community=self)

    @property
    def member_users(self):
        return User.objects.filter(is_active=True, u2ucp__community=self)

    @property
    def owners(self):
        from hs_access_control.models.privilege import PrivilegeCodes
        return User.objects.filter(is_active=True,
                                   u2ucp__community=self,
                                   u2ucp__privilege=PrivilegeCodes.OWNER)

    @property
    def public_resource_list(self):
        return BaseResource.objects.filter(r2grp__group__g2gcp__community=self,
                                           r2grp__group__gaccess__active=True)\
                                   .annotate(group_id=F("r2grp__group__id"),
                                             group_name=F("r2grp__group__name"),
                                             resource_id=F("short_id"),
                                             resource_title=F("title"),
                                             published=F("raccess__published"),
                                             public=F("raccess__public"),
                                             discoverable=F("raccess__discoverable"))\
                                   .values("group_id",
                                           "group_name",
                                           "resource_id",
                                           "resource_title",
                                           "resource_type",
                                           "discoverable",
                                           "public",
                                           "published")

    def get_effective_user_privilege(self, this_user):
        from hs_access_control.models.privilege import UserCommunityPrivilege
        return UserCommunityPrivilege.get_privilege(user=this_user, community=self)

    def get_effective_group_privilege(self, this_group):
        from hs_access_control.models.privilege import GroupCommunityPrivilege
        return GroupCommunityPrivilege.get_privilege(group=this_group, community=self)

    def get_groups_with_explicit_access(self, privilege, user=None):
        """
        Groups that contain resources that should be displayed for a community and/or user

        :param privilege: access privilege 1-3
        :param user: (optional) user whose groups should be excluded, because the user is
        already a member of the groups without community access.

        """
        if user is None:
            return Group.objects.filter(g2gcp__community=self, g2gcp__privilege=privilege)
        else:
            return Group.objects.filter(g2gcp__community=self, g2gcp__privilege=privilege)\
                    .exclude(g2ugp__user=user)

    def is_superuser(self, user):
        """
        Return whether a user is a superuser over the community self.
        """
        # prevent import loops
        from hs_access_control.models.privilege import GroupCommunityPrivilege, PrivilegeCodes
        return GroupCommunityPrivilege.objects.filter(community=self, group__g2ugp__user=user,
                                                      privilege=PrivilegeCodes.CHANGE).exists()

    def get_resources_with_explicit_access(self, user, group, privilege):
        """
        Get community resources available at a specific privilege for a given user and group.
        This routine is the root of the routines for rendering a community's holdings.
        The group determines which resources will be listed.
        The user determines the protection level. If any of the user's own groups are declared
        as supergroups, then the user has CHANGE over anything with CHANGE to its local group.
        Otherwise, the user has at most VIEW. If the user is not a member of a supergroup,
        listing may be overridden via the allow_view flag.o

        This listing routine has been separated from the main listing routines to avoid
        corrupting existing group views of resources, which have different protections than this.
        """
        from hs_access_control.models.privilege import PrivilegeCodes

        # if user is a member, member privileges apply regardless of superuser privileges
        # (superusers only obtain member privileges over every group in the community)
        if user in group.gaccess.members or self.is_superuser(user):
            if privilege == PrivilegeCodes.CHANGE:
                return BaseResource.objects.filter(raccess__immutable=False,
                                                   r2grp__group=group,
                                                   r2grp__privilege=privilege)
            else:
                return BaseResource.objects.filter(r2grp__group=group,
                                                   r2grp__privilege=privilege)

        # user is not a member of group and not a superuser
        elif privilege == PrivilegeCodes.CHANGE:  # requires superuser
            return BaseResource.objects.none()
        else:  # VIEW is requested for regular user
            return BaseResource.objects.filter(
                # if it's immutable, it just needs to be held by this group
                Q(raccess__immutable=True,
                  r2grp__group=group,
                  r2grp__group__g2gcp__community=self,
                  r2grp__group__g2gcp__allow_view=True,
                  r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=user) |
                # it's view if the group community privilege is VIEW
                Q(raccess__immutable=False,
                  r2grp__group=group,
                  r2grp__group__g2gcp__community=self,
                  r2grp__group__g2gcp__allow_view=True,
                  r2grp__group__g2gcp__community__c2gcp__privilege=PrivilegeCodes.VIEW,
                  r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=user) |
                # it's view if the target group's privilege is view
                Q(raccess__immutable=False,
                  r2grp__group=group,
                  r2grp__group__g2gcp__community=self,
                  r2grp__group__g2gcp__allow_view=True,
                  r2grp__privilege=PrivilegeCodes.VIEW,
                  r2grp__group__g2gcp__community__c2gcp__group__g2ugp__user=user)).distinct()
