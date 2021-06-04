from django.contrib.auth.models import User, Group
from django.db import models
from django.db import transaction
# from hs_core.models import BaseResource
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes


class GroupCommunityInvite(models.Model):
    group = models.ForeignKey(Group, editable=False, null=False)
    community = models.ForeignKey(Community, editable=False, null=False)
    community_owner = models.ForeignKey(User, editable=False, null=True, default=None)
    redeemed = models.BooleanField(editable=False, null=False, default=False)
    approved = models.BooleanField(editable=False, null=False, default=False)
    group_owner = models.ForeignKey(User, editable=False, null=True)
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    unique_together = ['group', 'community']

    @classmethod
    def create_or_update(cls, privilege=PrivilegeCodes.VIEW, **kwargs):
        assert('group' in kwargs)
        group = kwargs['group']
        assert(group.gaccess.active)

        assert('community' in kwargs)
        community = kwargs['community']

        assert('community_owner' in kwargs)
        community_owner = kwargs['community_owner']
        assert(community_owner.is_active)
        assert(community_owner.owns_community(community))

        del kwargs['community_owner']
        del kwargs['privilege']
        with transaction.atomic():
            invite_record, created = cls.objects.get_or_create(
                defaults={'community_owner': community_owner, 'privilege': privilege}, **kwargs)
            if not created:
                invite_record.community_owner = community_owner
                invite_record.privilege = privilege
                invite_record.save()
        # check for matching invitation
        request_record = GroupCommunityRequest.matching_request(community=community, group=group)
        # auto-approve if there's already an invite(!)
        if request_record is not None:
            invite_record.act(community_owner=community_owner, approve=True)
            request_record.act(group_owner=request_record.group_owner, approve=True)
        # auto-approve if auto_approve is True
        elif community.auto_approve:
            invite_record.act(community_owner=community.first_owner, approve=True)
        return invite_record, created

    @classmethod
    def active_requests(cls):
        return cls.objects.filter(redeemed=False)

    def act(self, group_owner, approved=False):
        community_owner = self.community_owner
        assert(group_owner.owns_group(self.group))
        assert(community_owner.owns_community(self.community))
        if approved:
            community_owner.share_community_with_group(self.community, self.group, self.privilege)
        self.group_owner = group_owner
        self.redeemed = True
        self.approved = approved
        self.save()

    @classmethod
    def matching_request(cls, **kwargs):
        matches = cls.objects.filter(redeemed=False)

        assert('group' in kwargs)
        matches = matches.filter(group=kwargs['group'])

        assert('community' in kwargs)
        matches = matches.filter(community=kwargs['community'])

        matches = list(matches)
        if matches:
            return matches[0]
        else:
            return None


class GroupCommunityRequest(models.Model):

    group = models.ForeignKey(Group, editable=False, null=False)
    community = models.ForeignKey(Community, editable=False, null=False)
    # requester
    group_owner = models.ForeignKey(User, editable=False, null=True)
    # responder
    community_owner = models.ForeignKey(User, editable=False, null=True)
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)
    redeemed = models.BooleanField(editable=False, default=False, null=False)
    approved = models.BooleanField(editable=False, null=False, default=False)
    unique_together = ['group', 'community']

    @classmethod
    def create_or_update(cls, privilege=PrivilegeCodes.VIEW, **kwargs):
        assert('group' in kwargs)
        group = kwargs['group']
        assert(group.gaccess.active)

        assert('community' in kwargs)
        community = kwargs['community']

        assert('group_owner' in kwargs)
        group_owner = kwargs['group_owner']
        assert(group_owner.is_active)
        assert(group_owner.owns_group(community))

        del kwargs['group_owner']
        del kwargs['privilege']
        with transaction.atomic():
            request_record, create = cls.objects.get_or_create(
                defaults={'group_owner': group_owner, 'privilege': privilege}, **kwargs)
            if not create:
                request_record.group_owner = group_owner
                request_record.privilege = privilege
                request_record.save()

        # check for matching invitation
        invite_record = GroupCommunityInvite.matching_request(community=community, group=group)
        # auto-approve if there's already an invite(!)
        if invite_record is not None:
            invite_record.act(group_owner=group_owner, approve=True)
            request_record.act(group_owner=invite_record.group_owner, approve=True)
        # auto-approve if auto_approve is True
        elif community.auto_approve:
            request_record.act(community_owner=community.first_owner, approve=True)
        return request_record, create

    @classmethod
    def active_requests(cls):
        return cls.objects.filter(redeemed=False)

    @classmethod
    def matching_request(cls, **kwargs):
        matches = cls.objects.filter(redeemed=False)

        assert('group' in kwargs)
        matches = matches.filter(group=kwargs['group'])

        assert('community' in kwargs)
        matches = matches.filter(community=kwargs['community'])

        matches = list(matches)
        if matches:
            return matches[0]
        else:
            return None

    def act(self, community_owner, approved=False):
        """ community_owner is the owner of the community """
        group_owner = self.group_owner
        assert(self.redeemed is False)
        assert(group_owner.owns_group(self.group))
        assert(community_owner.owns_community(self.community))
        assert(self.privilege == PrivilegeCodes.VIEW)
        if approved:
            community_owner.share_community_with_group(self.community, self.group, self.privilege)
        self.community_owner = community_owner
        self.redeemed = True
        self.approved = approved
        self.save()
