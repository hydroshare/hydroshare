from datetime import datetime

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models
from django.db.models import Exists, F, OuterRef, Q
from mezzanine.conf import settings
from sorl.thumbnail import ImageField as ThumbnailImageField, get_thumbnail

from hs_core.models import BaseResource
from theme.utils import get_upload_path_community
from ..enums import CommunityRequestEvents


###################################
# Communities of groups
###################################
class Community(models.Model):
    """ a placeholder class for a community of groups """
    name = models.TextField(null=False, blank=False)
    description = models.TextField(null=False, blank=False)
    email = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    purpose = models.TextField(null=True, blank=True)
    auto_approve_resource = models.BooleanField(null=False, default=False, blank=False, editable=False)
    auto_approve_group = models.BooleanField(null=False, default=False, blank=False, editable=False)
    date_created = models.DateTimeField(editable=False, auto_now_add=True)
    picture = ThumbnailImageField(upload_to=get_upload_path_community, null=True, blank=True)
    banner = ThumbnailImageField(upload_to=get_upload_path_community, null=True, blank=True)
    # whether community is available to be joined
    closed = models.BooleanField(null=False, default=False, blank=False, editable=False)
    # as part of approving a request for a new community, active is set to true.
    active = models.BooleanField(null=False, default=False, blank=False, editable=False)

    class Meta:
        ordering = ['date_created']

    def __str__(self):
        return self.name

    @property
    def member_groups(self):
        """ This returns all member groups """
        if not self.active:
            return Group.objects.none()
        return Group.objects.filter(gaccess__active=True,
                                    g2gcp__community=self)

    @property
    def member_users(self):
        if not self.active:
            return User.objects.none()
        return User.objects.filter(is_active=True, u2ucp__community=self)

    @property
    def owners(self):
        from hs_access_control.models.privilege import PrivilegeCodes
        if not self.active:
            return User.objects.none()
        return User.objects.filter(is_active=True,
                                   u2ucp__community=self,
                                   u2ucp__privilege=PrivilegeCodes.OWNER)

    def groups_with_public_resources(self):
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
        from hs_access_control.models import PrivilegeCodes
        if not self.active:
            return Group.objects.none()
        return self.member_groups\
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
        prepare a list of everything that gets displayed about each resource in a community.
        """
        # TODO: consider adding GenericRelation to expose reverse querying of metadata field.
        # TODO: This would enable fast querying of first author.
        # TODO: The side-effect of this is enabling deletion cascade, which shouldn't do anything.

        # import here to avoid import loops
        from hs_access_control.models.privilege import PrivilegeCodes

        # TODO: propagated resources should be owned by a member of the publishing group,
        # and not just any group in the community!
        if not self.active:
            return BaseResource.objects.none()
        res = BaseResource\
            .objects\
            .filter(Q(r2grp__group__g2gcp__community=self,
                      r2grp__group__gaccess__active=True,
                      r2urp__privilege=PrivilegeCodes.OWNER,  # owned by member of community
                      r2urp__user__u2ugp__group__g2gcp__community=self) |
                    Q(r2crp__community=self))\
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

    # TODO: this currently contains OWNER privilege only
    def get_effective_user_privilege(self, this_user):
        from hs_access_control.models.privilege import PrivilegeCodes, UserCommunityPrivilege
        if not self.active:
            return PrivilegeCodes.NONE
        return UserCommunityPrivilege.get_privilege(user=this_user, community=self)

    # TODO: this is never > VIEW.
    def get_effective_group_privilege(self, this_group):
        from hs_access_control.models.privilege import PrivilegeCodes, GroupCommunityPrivilege
        if not self.active:
            return PrivilegeCodes.NONE
        return GroupCommunityPrivilege.get_privilege(group=this_group, community=self)

    # TODO: this is never > VIEW.
    def get_effective_resource_privilege(self, this_resource):
        from hs_access_control.models.privilege import PrivilegeCodes, CommunityResourcePrivilege
        if not self.active:
            return PrivilegeCodes.NONE
        return CommunityResourcePrivilege.get_privilege(resource=this_resource, community=self)

    def get_groups_with_explicit_access(self, privilege, user=None):
        """
        Groups that contain resources that should be displayed for a community and/or user

        :param privilege: access privilege 1-3
        :param user: (optional) user whose groups should be excluded, because the user is
        already a member of the groups without community access.

        """
        if not self.active:
            return Group.objects.none()
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
        if not self.active:
            return False
        return GroupCommunityPrivilege.objects.filter(community=self, group__g2ugp__user=user,
                                                      privilege=PrivilegeCodes.CHANGE).exists()

    def get_resources_with_explicit_access(self, user, group, privilege):
        """
        Get community resources available at a specific privilege for a given user and group.
        This routine is the root of the routines for rendering a community's holdings.
        The group determines which resources will be listed.

        This listing routine has been separated from the main listing routines to avoid
        corrupting existing group views of resources, which have different protections than this.
        """
        from hs_access_control.models.privilege import PrivilegeCodes
        if not self.active:
            return BaseResource.objects.none()
        if group is None:
            # At this level, CHANGE is never allowed
            if privilege != PrivilegeCodes.VIEW:
                return BaseResource.objects.none()
            # direct access without group assocation with resource
            return BaseResource.objects.filter(
               Q(r2crp__community=self, r2crp__community__c2urp__user=user) |
               Q(r2crp__community=self, r2crp__community__c2gcp__group__g2ugp__user=user))\
                .distinct()

        # if user is a member, member privileges apply regardless of superuser privileges
        # (superusers only obtain member privileges over every group in the community)
        elif group.gaccess.members.filter(id=user.id).exists() or self.is_superuser(user):
            if privilege == PrivilegeCodes.CHANGE:
                return BaseResource.objects.filter(raccess__immutable=False,
                                                   r2grp__group=group,
                                                   r2grp__privilege=privilege)
            else:
                return BaseResource.objects.filter(r2grp__group=group,
                                                   r2grp__privilege=privilege)
        # now user is not a member of group and not a superuser
        elif privilege == PrivilegeCodes.CHANGE:  # requires superuser
            return BaseResource.objects.none()
        else:  # VIEW is requested for regular user via community
            return BaseResource.objects.none()

    @property
    def first_owner(self):
        from hs_access_control.models.privilege import UserCommunityPrivilege, PrivilegeCodes
        if not self.active:
            return User.objects.none()
        opriv = UserCommunityPrivilege.objects.filter(community=self, privilege=PrivilegeCodes.OWNER)\
            .order_by('start')
        opriv = list(opriv)
        if opriv:
            return opriv[0].user
        else:
            return None

# deprecated by RequestCommunity (TODO: need to clean up this commented code)
# class CommunityRequest(models.Model):
#     """ application for creating a community """
#     name = models.TextField(null=False, blank=False)
#     description = models.TextField(null=False, blank=False)
#     email = models.TextField(null=True, blank=True)
#     url = models.TextField(null=True, blank=True)
#     purpose = models.TextField(null=True, blank=True)
#     auto_approve = models.BooleanField(null=False, default=False, blank=False, editable=False)
#     date_requested = models.DateTimeField(editable=False, auto_now_add=True)
#     date_processed = models.DateTimeField(editable=False, null=True)
#     picture = models.ImageField(upload_to='community', null=True, blank=True)
#     # whether community is available to be joined
#     closed = models.BooleanField(null=False, default=True, blank=False, editable=False)
#     # user requesting community
#     owner = models.ForeignKey(User, null=True, editable=False)
#     # approval information: null means undecided
#     approved = models.NullBooleanField(null=True, default=None, blank=False, editable=False)

#     def __str__(self):
#         return self.name

#     def approve(self):
#         from hs_access_control.models.privilege import PrivilegeCodes, UserCommunityPrivilege
#         c = Community.objects.create(
#            name=self.name,
#            description=self.description,
#            email=self.email,
#            url=self.url,
#            purpose=self.purpose,
#            closed=self.closed)

#         self.approved = True
#         self.date_processed = datetime.now()
#         self.save()

#         # Must bootstrap access control system initially
#         # * Set the initial owner as given.
#         # * grantor is always admin.
#         admin = User.objects.get(username='admin')
#         owner = User.objects.get(username=self.owner)
#         UserCommunityPrivilege.share(community=c,
#                                      user=owner,
#                                      grantor=admin,
#                                      privilege=PrivilegeCodes.OWNER)

#         return "community '{}' approved and created.".format(self.name)

#     def decline(self):
#         self.approved = False
#         self.date_processed = datetime.now()
#         self.save()
#         return "community '{}' declined and not created.".format(self.name)


class RequestCommunity(models.Model):
    """A request to create a new community
    Note: As part of creating an instance this request, a new community gets created which is in inactive state
    When this request gets approved the community becomes active
    """
    community_to_approve = models.ForeignKey(Community, related_name='c2crequest')
    requested_by = models.ForeignKey(User, related_name='u2crequest')
    date_requested = models.DateTimeField(editable=False, auto_now_add=True)
    date_processed = models.DateTimeField(editable=False, null=True)
    approved = models.NullBooleanField(null=True, default=None, blank=False)
    decline_reason = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['date_requested']

    @classmethod
    def create_request(cls, request):
        """Helper to create a request for a new community"""

        # TODO: currently this method is not used for creating a community request.
        #  see hs_core/views/__init__.py view function 'request_new_community()' that is used for creating community
        #  If Mauriel ends of using this, then remove the view function 'request_new_community()'. Otherwise, this
        #  class method needs to be removed.

        from ..forms import RequestNewCommunityForm

        community_form = RequestNewCommunityForm(request.POST, request.FILES)
        if community_form.is_valid():
            new_community_request = community_form.save(request)
            # send email to hydroshare support (TODO: need to send it a designated admin email once
            #   we know the admin email)
            new_community_request.send_email(request_event=CommunityRequestEvents.CREATED)
            return new_community_request

        err_msg = f"Failed to make a request for a new community. Errors: {community_form.errors.as_json}"
        raise ValidationError(err_msg)

    def approve(self):
        """Helper to approve a request to create a new community
        Note: The caller of this function needs to check authorization for approval
        """
        assert self.approved is None

        self.date_processed = datetime.now()
        self.approved = True
        # upon approval the request the associated community is set to active
        self.community_to_approve.active = True
        self.community_to_approve.save()
        self.save()
        self.send_email(request_event=CommunityRequestEvents.APPROVED)

    def decline(self, reason):
        """Helper to reject a request to create a new community
        :param reason: reason for rejecting the request to create a community
        Note: The caller of this function needs to check authorization for approval
        """
        assert self.approved is None
        reason = reason.strip()
        if not reason:
            raise ValidationError("No reason for rejecting the request was provided")

        self.date_processed = datetime.now()
        self.approved = False
        self.decline_reason = reason
        # upon approval the request the associated community is set to active
        self.community_to_approve.active = False
        self.community_to_approve.save()
        self.save()
        self.send_email(request_event=CommunityRequestEvents.DECLINED)

    def remove(self):
        assert not self.community_to_approve.active
        # Note: deleting the community will cascade to delete self (RequestCommunity)
        self.community_to_approve.delete()

    def update_request(self, user, request):
        """Updates data for a community that is waiting for approval"""
        from ..forms import CommunityForm

        if self.approved is not None:
            raise ValidationError("Can't update this community request")

        community_to_update = self.community_to_approve
        cf = CommunityForm(data=request.POST)
        if cf.is_valid():
            frm_data = cf.cleaned_data
            community_to_update.name = frm_data['name']
            community_to_update.description = frm_data['description']
            community_to_update.purpose = frm_data['purpose']
            community_to_update.email = frm_data['email']
            community_to_update.url = frm_data['url']
            community_to_update.save()
        else:
            raise ValidationError("Community creation errors:{}.".format(cf.errors.as_json))

        if 'picture' in request.FILES:
            # resize uploaded logo image
            img = request.FILES['picture']
            img.image = get_thumbnail(img, 'x150', crop='center')
            community_to_update.picture = img
            community_to_update.save()

        # set the banner field of the newly created community
        if 'banner' in request.FILES:
            # resize uploaded banner image
            img = request.FILES['banner']
            img.image = get_thumbnail(img, '1200x200', crop='center')
            community_to_update.banner = img
            community_to_update.save()

    def send_email(self, request_event):
        if request_event == CommunityRequestEvents.CREATED:
            recipient_emails = [settings.DEFAULT_SUPPORT_EMAIL]
            subject = "New HydroShare Community Create Request"
            message = f"""Dear HydroShare Admin,
            <p>User {self.requested_by.first_name} is requesting creation of the following community.
            Please click on the link below to review this request.
            <p><a href="{self.get_absolute_url()}">{self.community_to_approve.name}</a></p>
            <p>HydroShare Team</p>
            """
        elif request_event == CommunityRequestEvents.DECLINED:
            recipient_emails = [self.requested_by.email]
            subject = "HydroShare Community Create Request Declined"
            message = f"""Dear {self.requested_by.first_name},
            <p>Sorry to inform you that your request to create the community
            <a href="{self.get_absolute_url()}">{self.community_to_approve.name}</a> was not approved due to
            the reason stated below:</p>
            <p>{self.decline_reason}</p>
            <p>HydroShare Team</p>
            """
        else:
            # community request approved event
            recipient_emails = [self.requested_by.email]
            subject = "HydroShare Community Create Request Approved"
            message = f"""Dear {self.requested_by.first_name},
            <p>Glad to inform you that your request to create the community
            <a href="{self.get_absolute_url(request=False)}">{self.community_to_approve.name}</a> has been approved.</p>
            <p>HydroShare Team</p>
            """
        send_mail(subject=subject, message=message, html_message=message, from_email=settings.DEFAULT_FROM_EMAIL,
                  recipient_list=recipient_emails, fail_silently=True)

    def get_absolute_url(self, request=True):
        from hs_core.hydroshare import current_site_url
        site_domain = current_site_url()
        if request:
            # get the url for the community request
            absolute_url = f"{site_domain}/communities/manage-requests/{self.id}"
        else:
            # get the url for the community
            absolute_url = f"{site_domain}/communities/{self.community_to_approve.id}"

        return absolute_url

    @classmethod
    def all_requests(cls):
        """Gets a queryset of all community requests"""
        return cls.objects.select_related('community_to_approve')

    @classmethod
    def pending_requests(cls):
        """Gets a queryset of all pending community requests"""
        return cls.objects.filter(Q(approved=None)).select_related('community_to_approve')
