from django.contrib.auth.models import User, Group
from django.db import models
from hs_core.models import BaseResource
from django.db.models import Q, F
from django.contrib.contenttypes.models import ContentType

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
    def public_resources(self):
        """
        prepare a list of everything that gets displayed about each resource in a community.
        """
        # TODO: consider adding GenericRelation to expose reverse querying of metadata field.
        # TODO: This would enable fast querying of first author.
        # TODO: The side-effect of this is enabling deletion cascade, which shouldn't do anything.
        res = BaseResource.objects.filter(r2grp__group__g2gcp__community=self,
                                          r2grp__group__gaccess__active=True)\
                                  .filter(Q(raccess__public=True) |
                                          Q(raccess__published=True) |
                                          Q(raccess__discoverable=True))\
                                  .annotate(group_name=F("r2grp__group__name"),
                                            group_id=F("r2grp__group__id"),
                                            public=F("raccess__public"),
                                            published=F("raccess__published"),
                                            discoverable=F("raccess__discoverable"))

        res = res.only('title', 'resource_type', 'created', 'updated')
        # # Can't do the following because the content model is polymorphic.
        # # This is documented as only working for monomorphic content_type
        # res = res.prefetch_related("content_object___title",
        #                            "content_object___description",
        #                            "content_object__creators")
        # We want something that is not O(# resources + # content types).
        # O(# content types) is sufficiently faster.
        # The following strategy is documented here:
        # https://blog.roseman.org.uk/2010/02/22/django-patterns-part-4-forwards-generic-relations/

        # collect generics from resources
        generics = {}
        for item in res:
            generics.setdefault(item.content_type.id, set()).add(item.object_id)

        # fetch all content types in one query
        content_types = ContentType.objects.in_bulk(generics.keys())

        # build a map between content types and the objects that use them.
        relations = {}
        for ct, fk_list in generics.items():
            ct_model = content_types[ct].model_class()
            relations[ct] = ct_model.objects.in_bulk(list(fk_list))

        # force-populate the cache of content type objects.
        for item in res:
            setattr(item, '_content_object_cache',
                    relations[item.content_type.id][item.object_id])

        # Detailed notes:
        # This subverts chained lookup by pre-populating the content object cache
        # that is populated by an object reference. It is very dependent upon the
        # implementation of GenericRelation and its pre-fetching strategy.
        # Thus it is quite brittle and vulnerable to major revisions of Generics.

        return res

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
