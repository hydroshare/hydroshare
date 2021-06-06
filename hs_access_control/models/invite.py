from django.contrib.auth.models import User, Group
from django.db import models
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes


class GroupCommunityInvite(models.Model):
    '''
    A mechanism for handling Invitations from a community owner to a group owner.
    * The community owner creates a GroupCommunityInvite.
    * The group owner uses GroupCommunityInvite.act() to respond.
    '''

    # target
    group = models.ForeignKey(Group, editable=False, null=False)
    # source
    community = models.ForeignKey(Community, editable=False, null=False)
    # invitee
    group_owner = models.ForeignKey(User, editable=False, null=True, default=None, related_name='invite_gcg')
    # inviter
    community_owner = models.ForeignKey(User, editable=False, null=True, related_name='invite_gcc')

    # when request was made
    when_requested = models.DateTimeField(editable=False, null=True, default=None)
    # when response was given
    when_responded = models.DateTimeField(editable=False, null=True, default=None)

    # Privilege with which to share: default is VIEW
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    # redeemed is True if already acted upon
    redeemed = models.BooleanField(editable=False, null=False, default=False)

    # approved is True if redeemed is True and the request was approved.
    approved = models.BooleanField(editable=False, null=False, default=False)

    # only one request active at a time per pair
    unique_together = ['group', 'community']

    def __str__(self):
        return "GroupCommunityInvite: community='{}' by '{}', group='{}' by '{}'"\
            .format(str(self.community), str(self.community_owner),
                    str(self.group), str(self.group_owner))

    def save(self, *args, **kwargs):
        '''
        On save, update timestamps.
        See discussion of auto_now and auto_now_add in stack overflow for details
        '''
        if not self.id:  # when created
            self.when_requested = timezone.now()
        return super(GroupCommunityInvite, self).save(*args, **kwargs)

    @classmethod
    def create_or_update(cls, **kwargs):

        '''
        Invite a group into a community. This can only be done by a community owner.
        :param group: target Group.
        :param community: target Community.
        :param community_owner: a User doing the inviting.

        Usage:
            GroupCommunityInvite.create_or_update(group={X}, community={Y}, community_owner={Z})

        Return: returns a triple of values
        * message: a status message for the community owner using this routine.
        * invitation: the invitation object of type GroupCommunityInvite.
        * created: whether the invitation new. If false, it existed already.

        Theory of operation: This routine ensures that there is never more than one
        invitation per group/community pair, by finding existing records and updating
        them as needed.

        As well, there are several avenues to automatic acceptance of an invitation.
        1. If a group owner has independently requested access to the Community.
        2. If the community owner also owns the group.

        The second part, after making the invitation, is that the group owner has to respond.
        This is enabled by several functions:
        * GroupCommunityInvite.active_requests(): a list of active requests
        * request.act(group_owner={X}, approved={Y}): act on a specific request.

        '''
        if __debug__:
            assert('group' in kwargs)
            assert(isinstance(kwargs['group'], Group))
            assert(kwargs['group'].gaccess.active)
            assert('community_owner' in kwargs)
            assert(isinstance(kwargs['community_owner'], User))
            assert(kwargs['community_owner'].is_active)
            assert('community' in kwargs)
            assert(isinstance(kwargs['community'], Community))
            assert(kwargs['community_owner'].uaccess.owns_community(kwargs['community']))

        if 'privilege' in kwargs:
            privilege = kwargs['privilege']
            privilege = int(privilege)
            if privilege != PrivilegeCodes.VIEW:
                raise PermissionDenied("Only view privilege may be requested")
        else:
            privilege = PrivilegeCodes.VIEW

        group = kwargs['group']
        community = kwargs['community']
        community_owner = kwargs['community_owner']

        # first check whether the group is already in the community (!)
        if group in community.member_groups:
            message = "Group '{}' is already part of community '{}'."\
                .format(group.name, community.name)
            return message, None, True

        # default success message
        message = "Invitation created for group '{}' ({}) to join community '{}' ({})."\
            .format(group.name, group.id, community.name, community.id)

        del kwargs['community_owner']
        with transaction.atomic():
            invite_record, created = cls.objects.get_or_create(
                defaults={'community_owner': community_owner, 'privilege': privilege}, **kwargs)
            if not created:
                invite_record.community_owner = community_owner
                invite_record.privilege = privilege
                invite_record.redeemed = False
                invite_record.when_requested = timezone.now()
                invite_record.when_responded = None
                invite_record.save()
                message = "Invitation updated for group '{}' ({}) to join community '{}' ({})."\
                    .format(group.name, group.id, community.name, community.id)

        # check for matching request;
        request_record = GroupCommunityRequest.matching_request(community=community, group=group)
        # auto-approve if there's already a request(!)
        if request_record is not None:
            invite_record.act(group_owner=request_record.group_owner, approved=True)
            request_record.act(community_owner=community_owner, approved=True)
            message = "Invitation auto-approved for group '{}' ({}) to join community '{}' ({})"\
                " because there is a matching request."\
                .format(group.name, group.id, community.name, community.id)

        # auto-approve if the owner is the group owner
        elif community_owner.uaccess.owns_group(group):
            invite_record.act(group_owner=community_owner, approved=True)
            message = "Invitation auto-approved for group '{}' ({}) to join community '{}' ({})"\
                " because you also own the group."\
                .format(group.name, group.id, community.name, community.id)

        # normal completion
        return message, invite_record, created

    def act(self, group_owner, approved=False):
        '''
        Act on a Group/Community invitation.

        Arguments:
        :param group_owner: owner of the group
        :param approved: whether the owner accepts the invitation or not.

        Return value: This returns a triple:
        * message: a message to give to the group owner.
        * request: the modified request object.
        * success: whether the action was taken successfully.

        Theory of operation: This is done by the group owner after the invitation is issued
        the community owner. As time may have passed, there are multiple ways this can fail,
        e.g., the community owner in question might not own the community any more!
        '''
        community_owner = self.community_owner

        if not group_owner.uaccess.owns_group(self.group):
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Invitation from community '{}' to group '{}': you do not own the group."\
                .format(self.community.name, self.group.name)
            return message, self, False

        if not community_owner.uaccess.owns_community(self.community):
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Invitation from community '{}' to group '{}': inviter no longer owns the community."\
                .format(self.community.name, self.group.name)
            return message, self, False

        if self.privilege != PrivilegeCodes.VIEW:
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Invitation from community '{}' to group '{}': only view privilege is allowed."\
                .format(self.community.name, self.group.name)
            return message, self, False

        if self.redeemed:
            message = "Invitation from community '{}' to group '{}': already acted upon."\
                .format(self.community.name, self.group.name)
            return message, self, False

        # now we know the request is valid: act on it
        if approved:
            community_owner.uaccess.share_community_with_group(self.community, self.group, self.privilege)

        self.group_owner = group_owner
        self.redeemed = True
        self.approved = approved
        self.when_responded = timezone.now()
        self.save()
        message = "Invitation from community '{}' to group '{}' {}.".format(
            self.community.name, self.group.name, 'approved' if approved else 'declined')
        return message, self, True

    @classmethod
    def active_requests(cls, group_owner=None):
        '''
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests to act upon. To do this,
        list the current user as group_owner
        '''
        requests = cls.objects.filter(redeemed=False)
        if group_owner is not None:
            assert(isinstance(group_owner, User))
            requests = requests.filter(group__g2ugp__user=group_owner,
                                       group__g2ugp__privilege=PrivilegeCodes.OWNER)
        return requests

    @classmethod
    def matching_request(cls, **kwargs):
        '''
        Returns the unique request, if any concerning a Group/Community pair.

        Arguments
        :community: the Community object
        :group: the Group object

        This either returns a single object or None if there is none.
        '''
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

    @classmethod
    def remove(cls, **kwargs):
        '''
        Remove a group from a community. This can only be done by a community owner.
        :param group: target group.
        :param community: target community.
        :param community_owner: community_owner requesting removal of the object.

        Usage:
            GroupCommunityPrivilege.remove(group={X}, community={Y}, community_owner={Z})

        Return values: returns a pair of values
        * message: a status message for the user.
        * success: whether the removal succeeded.

        '''
        if __debug__:
            assert('group' in kwargs)
            assert(isinstance(kwargs['group'], Group))
            assert(kwargs['group'].gaccess.active)
            assert('community_owner' in kwargs)
            assert(isinstance(kwargs['community_owner'], User))
            assert(kwargs['community_owner'].is_active)
            assert('community' in kwargs)
            assert(isinstance(kwargs['community'], Community))

        group = kwargs['group']
        community = kwargs['community']
        community_owner = kwargs['community_owner']

        # first check whether the group is already in the community (!)
        if group not in community.member_groups:
            message = "Group '{}' is not in community '{}'."\
                .format(group.name, community.name)
            return message, True

        if not community_owner.owns_community(community):
            message = "User {} does not own community '{}'"\
                .format(community_owner.username, community.name)
            return message, False

        community_owner.uaccess_unshare_community_with_group(community, group)
        message = "Group '{}' ({}) removed from community '{}' ({})."\
            .format(group.name, group.id, community.name, community.id)
        return message, True


class GroupCommunityRequest(models.Model):
    '''
    A mechanism for handling requests from a group owner to a community owner.
    * The group owner creates a GroupCommunityRequest
    * The community owner uses GroupCommunityRequest.act() to respond.
    '''
    # source
    group = models.ForeignKey(Group, editable=False, null=False)
    # target
    community = models.ForeignKey(Community, editable=False, null=False)
    # requester
    group_owner = models.ForeignKey(User, editable=False, null=True, related_name='request_gcg')
    # responder
    community_owner = models.ForeignKey(User, editable=False, null=True, related_name='request_gcc')

    # when request was made
    when_requested = models.DateTimeField(editable=False, null=True, default=None)
    # when response was given
    when_responded = models.DateTimeField(editable=False, null=True, default=None)

    # Privilege with which to share: default is VIEW
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    # redeemed is True if already acted upon
    redeemed = models.BooleanField(editable=False, default=False, null=False)

    # approved is True if redeemed is True and the request was approved.
    approved = models.BooleanField(editable=False, null=False, default=False)

    # only one request active at a time per pair
    unique_together = ['group', 'community']

    def __str__(self):
        return "GroupCommunityRequest: community='{}' by '{}', group='{}' by '{}'"\
            .format(str(self.community), str(self.community_owner),
                    str(self.group), str(self.group_owner))

    def save(self, *args, **kwargs):
        ''' On save, update initial timestamp '''
        ''' See discussion of auto_now and auto_now_add in stack overflow for details '''
        if not self.id:  # when created
            self.when_requested = timezone.now()
        return super(GroupCommunityRequest, self).save(*args, **kwargs)

    @classmethod
    def create_or_update(cls, **kwargs):

        '''
        Request access to a community by a group. This can only be done by a group owner.
        :param group: target Group.
        :param community: target Community.
        :param group_owner: a User making the request.

        Usage:
            GroupCommunityRequest.create_or_update(group={X}, community={Y}, group_owner={Z})

        Return: returns a triple of values
        * message: a status message for the group owner using this routine.
        * invitation: the invitation object of type GroupCommunityRequest.
        * created: whether the request is new. If false, it existed already.

        Theory of operation: This routine ensures that there is never more than one
        request per group/community pair, by finding existing records and updating
        them as needed.

        As well, there are several avenues to automatic acceptance of an invitation.
        1. If a community owner has independently invited the group.
        2. If the group owner also owns the community.
        3. If auto_approve is True for the community.

        The second part, after making the invitation, is that the community owner has to respond.
        This is enabled by several functions:
        * GroupCommunityRequest.active_requests(): a list of active requests
        * request.act(community_owner={X}, approved={Y}): act on a specific request.

        '''
        if __debug__:
            assert('group' in kwargs)
            assert(isinstance(kwargs['group'], Group))
            assert(kwargs['group'].gaccess.active)
            assert('group_owner' in kwargs)
            assert(isinstance(kwargs['group_owner'], User))
            assert(kwargs['group_owner'].is_active)
            assert(kwargs['group_owner'].uaccess.owns_group(kwargs['group']))
            assert('community' in kwargs)
            assert(isinstance(kwargs['community'], Community))

        if 'privilege' in kwargs:
            privilege = kwargs['privilege']
            privilege = int(privilege)
            if privilege != PrivilegeCodes.VIEW:
                raise PermissionDenied("Only view privilege may be requested")
        else:
            privilege = PrivilegeCodes.VIEW

        group = kwargs['group']
        group_owner = kwargs['group_owner']
        community = kwargs['community']

        # first check whether the group is already in the community (!)
        if group in community.member_groups:
            message = "Group '{}' is already part of community '{}'."\
                .format(group.name, community.name)
            return message, None, True

        # default success message
        message = "Request created for group '{}' ({}) to join community '{}' ({})."\
            .format(group.name, group.id, community.name, community.id)

        del kwargs['group_owner']
        with transaction.atomic():
            request_record, created = cls.objects.get_or_create(
                defaults={'group_owner': group_owner, 'privilege': privilege}, **kwargs)
            if not created:
                request_record.group_owner = group_owner
                request_record.privilege = privilege
                request_record.redeemed = False
                request_record.when_requested = timezone.now()
                request_record.when_responded = None
                request_record.save()
                message = "Request updated for group '{}' ({}) to join community '{}' ({})."\
                    .format(group.name, group.id, community.name, community.id)

        # check for matching invitation
        invite_record = GroupCommunityInvite.matching_request(community=community, group=group)
        # auto-approve if there's already an invite(!)
        if invite_record is not None:
            invite_record.act(group_owner=group_owner, approved=True)
            request_record.act(community_owner=invite_record.community_owner, approved=True)
            message = "Request approved for group '{}' ({}) to join community '{}' ({})"\
                " because there is a matching invitation."\
                .format(group.name, group.id, community.name, community.id)

        # auto-approve if the owner is the community owner
        elif group_owner.uaccess.owns_community(community):
            request_record.act(community_owner=group_owner, approved=True)
            message = "Request auto-approved for group '{}' ({}) to join community '{}' ({})"\
                " because you also own the community."\
                .format(group.name, group.id, community.name, community.id)

        # auto-approve if auto_approve is True
        elif community.auto_approve:
            request_record.act(community_owner=community.first_owner, approved=True)
            message = "Request auto-approved for group '{}' ({}) to join community '{}' ({})."\
                .format(group.name, group.id, community.name, community.id)

        # normal completion
        return message, request_record, created

    def act(self, community_owner, approved=False):
        '''
        Act on a Group/Community request.

        Arguments:
        :param community_owner: owner of the community
        :param approved: whether the community owner accepts the request or not.

        Return value: This returns a triple:
        * message: a message to give to the community owner.
        * request: the modified request object.
        * success: whether the action was taken successfully.

        Theory of operation: This is done by the community owner after the request is made by
        the group owner. As time may have passed, there are multiple ways this can fail,
        e.g., the group owner in question might not own the group any more!
        '''
        group_owner = self.group_owner
        if not group_owner.uaccess.owns_group(self.group):
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Request from group '{}' to join community '{}': requester no longer owns the group."\
                .format(self.group.name, self.community.name)
            return message, self, False
        if not community_owner.uaccess.owns_community(self.community):
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Request from group '{}' to join community '{}': you do not own the community."\
                .format(self.group.name, self.community.name)
            return message, self, False
        if self.privilege != PrivilegeCodes.VIEW:
            self.approved = False
            self.redeemed = True
            self.when_responded = timezone.now()
            self.save()
            message = "Request from group '{}' to join community '{}': only view privilege is allowed."\
                .format(self.group.name, self.community.name)
            return message, self, False
        if self.redeemed:
            message = "Request from group '{}' to join community '{}': already acted upon."\
                .format(self.group.name, self.community.name)
            return message, self, False

        # now we know the request is valid: act on it
        if approved:
            community_owner.uaccess.share_community_with_group(self.community, self.group, self.privilege)
        self.community_owner = community_owner
        self.redeemed = True
        self.approved = approved
        self.when_responded = timezone.now()
        self.save()
        message = "Request from group '{}' to join community '{}' {}."\
            .format(self.group.name,
                    self.community.name,
                    'approved' if approved else 'declined')
        return message, self, True

    @classmethod
    def active_requests(cls, community_owner=None):
        '''
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests to act upon.
        '''
        requests = cls.objects.filter(redeemed=False)
        if community_owner is not None:
            assert(isinstance(community_owner, User))
            requests = requests.filter(community__c2ucp__user=community_owner,
                                       community__c2ucp__privilege=PrivilegeCodes.OWNER)
        return requests

    @classmethod
    def matching_request(cls, **kwargs):
        '''
        Returns the unique request, if any concerning a Group/Community pair.

        Arguments
        :community: the Community object
        :group: the Group object

        This either returns a single object or None if there is none.
        '''
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
