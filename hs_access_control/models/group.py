from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import Q, F, Exists, OuterRef
from django.contrib.contenttypes.models import ContentType

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes, UserGroupPrivilege
from hs_access_control.models.community import Community
from sorl.thumbnail import ImageField as ThumbnailImageField
from theme.utils import get_upload_path_group


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
# * GroupAccess.view_resources and GroupAccess.edit_resources
#   do not reflect community privileges.
# * GroupAccess.get_resources_with_explicit_access does *not* reflect
#   community privileges.
# (Revised Sept 17, 2021)
#############################################
class GroupMembershipRequest(models.Model):
    request_from = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ru2gmrequest')

    # when user is requesting to join a group this will be blank
    # when a group owner is sending an invitation, this field will represent the inviting user
    invitation_to = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                      related_name='iu2gmrequest')
    group_to_join = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='g2gmrequest')
    date_requested = models.DateTimeField(editable=False, auto_now_add=True)
    explanation = models.TextField(null=True, blank=True, max_length=300)
    redeemed = models.BooleanField(default=False)


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
    group = models.OneToOneField(Group, on_delete=models.CASCADE,
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
                                       help_text='whether group description is discoverable by everyone')

    public = models.BooleanField(default=True,
                                 editable=False,
                                 help_text='whether group members can be listed by everyone')

    shareable = models.BooleanField(default=True,
                                    editable=False,
                                    help_text='whether group can be shared by non-owners')

    auto_approve = models.BooleanField(default=False,
                                       editable=False,
                                       help_text='whether group membership can be auto approved')

    requires_explanation = models.BooleanField(default=False, editable=False,
                                               help_text='whether membership requests include explanation')

    description = models.TextField(null=False, blank=False)
    purpose = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    picture = ThumbnailImageField(upload_to=get_upload_path_group, null=True, blank=True)

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
                                   u2ugp__privilege=PrivilegeCodes.OWNER).select_related('userprofile')

    @property
    def __edit_users_of_group(self):
        """
        Q expression for users who can edit a group according to group privilege
        """
        return Q(is_active=True,
                 u2ugp__group=self.group,
                 u2ugp__privilege__lte=PrivilegeCodes.CHANGE)

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
    def view_users(self):
        """
        Return list of users who can add members to a group

        :return: list of users

        This eliminates duplicates due to multiple memberships,
        unlike members, which just lists explicit group members.
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
                                   u2ugp__privilege__lte=PrivilegeCodes.VIEW).select_related('userprofile')

    @property
    def viewers(self):
        """ viewers are group members """
        return User.objects.filter(
            Q(is_active=True)
            & (Q(u2ugp__group__gaccess__active=True,
                 u2ugp__group=self.group))).distinct()

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
    def __owned_resources_of_group(self):
        """
        resources owned by some group member

        Used in queries of BaseResource
        """
        return Q(r2grp__group=self.group,
                 r2urp__user__u2ugp__group=self.group,
                 r2urp__privilege=PrivilegeCodes.OWNER)

    @property
    def view_resources(self):
        """
        QuerySet of resources held by group.

        :return: QuerySet of resource objects held by group.

        """
        return BaseResource.objects.filter(self.__view_resources_of_group).select_related('raccess')

    @property
    def edit_resources(self):
        """
        QuerySet of resources that can be edited by group.

        :return: List of resource objects that can be edited by this group.

        These include resources that are directly editable, as well as those editable
        via membership in a group.
        """
        return BaseResource.objects.filter(self.__edit_resources_of_group).select_related('raccess')

    @property
    def owned_resources(self):
        """
        QuerySet of resources that are owned by some group member

        :return: List of resource objects owned by some group member.

        This is independent of whether the resource is editable by the group.

        """
        return BaseResource.objects.filter(self.__owned_resources_of_group).select_related('raccess')

    @property
    def group_membership_requests(self):
        """
        get a list of pending group membership requests for this group (self)
        :return: QuerySet
        """

        return GroupMembershipRequest.objects.filter(group_to_join=self.group,
                                                     group_to_join__gaccess__active=True,
                                                     redeemed=False)

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
                                                 r2grp__group=self.group)
                                               | Q(raccess__immutable=True,
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

    @classmethod
    def groups_with_public_resources(cls):
        """ Return the list of groups that have discoverable or public resources
            These must contain at least one resource that is discoverable and
            is owned by a group member.

            This query is subtle. See
                https://medium.com/@hansonkd/\
                the-dramatic-benefits-of-django-subqueries-and-annotations-4195e0dafb16
            for details of how this improves performance.

           As a short summary, all we need to know is that one resource exists.
           This is not possible to notate in the main query except through an annotation.
           However, that annotation is really efficient, and is implemented as a postgres
           subquery. This is a Django 1.11 extension.
        """
        return Group.objects\
            .annotate(
                has_public_resources=Exists(
                    BaseResource.objects.filter(
                        raccess__discoverable=True,
                        r2grp__group__id=OuterRef('id'),
                        r2urp__user__u2ugp__group__id=OuterRef('id'),
                        r2urp__privilege=PrivilegeCodes.OWNER)))\
            .filter(has_public_resources=True)\
            .order_by('name')

    @property
    def public_resources(self):
        """
        prepare a list of everything that gets displayed about each resource in a group.

        Based upon hs_access_control/models/community.py:Community:public_resources
        """
        res = BaseResource.objects.filter(r2grp__group__gaccess=self,
                                          r2grp__group__gaccess__active=True)\
            .filter(Q(raccess__public=True)
                    | Q(raccess__published=True)
                    | Q(raccess__discoverable=True))\
            .filter(r2urp__privilege=PrivilegeCodes.OWNER,
                    r2urp__user__u2ugp__group=self.group)\
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
        content_types = ContentType.objects.in_bulk(list(generics.keys()))

        # build a map between content types and the objects that use them.
        relations = {}
        for ct, fk_list in list(generics.items()):
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

    @property
    def first_owner(self):
        opriv = UserGroupPrivilege.objects.filter(group=self.group, privilege=PrivilegeCodes.OWNER)\
            .order_by('start')
        opriv = list(opriv)
        if opriv:
            return opriv[0].user
        else:
            return None
