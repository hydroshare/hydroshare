from django.contrib.auth.models import User, Group
from django.db import models, transaction
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from hs_access_control.models.community import Community
from hs_access_control.models.privilege import PrivilegeCodes


class InitiatorCodes(object):
    NONE = 0
    RESOURCE = 1
    USER = 2
    GROUP = 3
    COMMUNITY = 4
    CHOICES = (
        (RESOURCE, 'Resource'),
        (USER, 'User'),
        (GROUP, 'Group'),
        (COMMUNITY, 'Community')
    )
    # Names of privileges for printing
    NAMES = ('Unspecified', 'Resource', 'User', 'Group', 'Community')


class GroupCommunityRequest(models.Model):
    '''
    A mechanism for handling Invitations from a community owner to a group owner.
    * The community owner creates a GroupCommunityRequest.
    * The group owner uses GroupCommunityRequest.act() to respond.
    '''

    # target
    group = models.ForeignKey(Group, on_delete=models.CASCADE, editable=False, null=False)
    # source
    community = models.ForeignKey(Community, on_delete=models.CASCADE, editable=False, null=False)
    # invitee
    group_owner = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, null=True, default=None,
                                    related_name='invite_gcg')
    # inviter
    community_owner = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, null=True,
                                        related_name='invite_gcc')

    # when request was made
    when_requested = models.DateTimeField(editable=False, null=True, default=None)
    # when response was given
    when_responded = models.DateTimeField(editable=False, null=True, default=None)

    # Privilege with which to share: default is VIEW
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    null=True)

    # redeemed is True if already acted upon
    redeemed = models.BooleanField(editable=False, null=False, default=False)

    # approved is True if redeemed is True and the request was approved.
    approved = models.BooleanField(editable=False, null=False, default=False)

    # only one request active at a time per pair
    unique_together = ['group', 'community']

    def __str__(self):
        return "GroupCommunityRequest: community='{}' owned by '{}', group='{}' owned by '{}'"\
            .format(str(self.community), str(self.community_owner),
                    str(self.group), str(self.group_owner))

    def save(self, *args, **kwargs):
        '''
        On save, update timestamps.
        See discussion of auto_now and auto_now_add in stack overflow for details
        '''
        if not self.id:  # when created
            self.when_requested = timezone.now()
        return super(GroupCommunityRequest, self).save(*args, **kwargs)

    @classmethod
    def create_or_update(cls, **kwargs):
        '''
        Request a group to be included in a community. This can only be done by agreement between
        a community owner and a group owner.

        :param group: target Group.
        :param community: target Community.
        :param requester: a User doing the requesting. Must own the community or the group.

        Usage:
            GroupCommunityRequest.create_or_update(group={X}, community={Y}, requester={Z})

        Return: returns a triple of values
        * message: a status message for the community owner using this routine.
        * request: the request object of type GroupCommunityRequest.
        * approved: whether the request was approved. If False, it was only queued.

        Theory of operation: This routine ensures that there is never more than one
        request per group/community pair, by finding existing records and updating
        them as needed. A record is deemed incomplete until both owners have signed off.

        As well, there are several avenues to automatic approval of an invitation.
        1. If there is already a signoff by the other owner.
        2. If the requester owns both community and group.
        3. If the community owner has checked "auto_accept" in the community configuration.

        The second part, after making the invitation, is that the other owner has to respond, by
        making his/her own request, so that the requests can be combined and implemented.

        This is enabled by several functions:
        * GroupCommunityRequest.active_requests(requester=User):
          active requests awaiting a user's response.
        * GroupCommunityRequest.pending(requester={X}, group={Y}, community={Z}):
          requests that are pending for a user.

        '''
        if __debug__:
            assert ('group' in kwargs)
            assert (isinstance(kwargs['group'], Group))
            assert (kwargs['group'].gaccess.active)
            assert ('community' in kwargs)
            assert (isinstance(kwargs['community'], Community))
            assert ('requester' in kwargs)
            assert (isinstance(kwargs['requester'], User))

        approved = False  # whether auto-approved
        group = kwargs['group']
        community = kwargs['community']
        requester = kwargs['requester']

        # first check whether the group is already in the community (!)
        if group in community.member_groups:
            message = "Group '{}' is already connected to community '{}'."\
                .format(group.name, community.name)
            return message, True

        # requester owns both.
        if requester.uaccess.owns_community(community) and requester.uaccess.owns_group(group):
            community_owner = requester
            group_owner = requester

            if 'privilege' in kwargs:  # only set by community owner
                privilege = kwargs['privilege']
                privilege = int(privilege)
                if privilege != PrivilegeCodes.VIEW:
                    raise PermissionDenied("Only view privilege may be requested")
            else:
                privilege = PrivilegeCodes.VIEW

            # Get the transaction record, if any
            with transaction.atomic():
                request, created = cls.objects.get_or_create(
                    defaults={'community_owner': community_owner, 'privilege': privilege},
                    group=group, community=community)

            request.community_owner = community_owner
            request.group_owner = group_owner
            request.redeemed = True
            request.approved = True
            request.privilege = privilege
            request.when_responded = timezone.now()
            request.save()
            approved = True
            community_owner.uaccess.share_community_with_group(
                request.community, request.group, request.privilege)
            message = "Request approved to connect group '{}' to community '{}'"\
                " because you own both."\
                .format(request.group.name, request.community.name)

            # normal completion
            return message, approved

        elif requester.uaccess.owns_community(community):
            community_owner = requester

            if 'privilege' in kwargs:  # only set by community owner
                privilege = kwargs['privilege']
                privilege = int(privilege)
                if privilege != PrivilegeCodes.VIEW:
                    raise PermissionDenied("Only view privilege may be requested")
            else:
                privilege = PrivilegeCodes.VIEW

            # default success message
            message = "Request created to connect group '{}' to community '{}'."\
                .format(group.name, community.name)

            with transaction.atomic():
                request, created = cls.objects.get_or_create(
                    defaults={'community_owner': community_owner, 'privilege': privilege},
                    group=group, community=community)

            # auto-approve if there's already a request(!)
            if request.group_owner is not None and request.redeemed is False:
                request.community_owner = community_owner
                request.privilege = privilege
                request.redeemed = True
                request.approved = True
                request.when_responded = timezone.now()
                request.save()
                approved = True
                community_owner.uaccess.share_community_with_group(
                    request.community, request.group, request.privilege)
                message = "Request approved to connect group '{}' to community '{}'"\
                    " because there is a matching request."\
                    .format(group.name, community.name)

            # refresh request: this has the side effect of disabling any prior denials
            elif not created:
                request.community_owner = community_owner
                request.privilege = privilege
                request.redeemed = False
                request.approved = False
                request.when_requested = timezone.now()
                request.when_responded = None
                request.save()
                message = "Request updated: connect group '{}' to community '{}'."\
                    .format(group.name, community.name)

            # normal completion
            return message, approved

        elif requester.uaccess.owns_group(group):
            group_owner = requester

            # default success message
            message = "Request created to connect group '{}' to community '{}'."\
                .format(group.name, community.name)

            with transaction.atomic():
                request, created = cls.objects.get_or_create(
                    defaults={'group_owner': group_owner}, community=community, group=group)

            # auto-approve if there's already an invite(!)
            if request.community_owner is not None and request.privilege is not None:
                request.group_owner = group_owner
                request.redeemed = True
                request.approved = True
                request.when_responded = timezone.now()
                request.save()
                approved = True
                request.community_owner.uaccess.share_community_with_group(
                    request.community, request.group, request.privilege)
                message = "Request approved to connect group '{}' to community '{}'"\
                    " because there is a matching request."\
                    .format(group.name, community.name)

            # auto-approve if auto_approve is True
            elif community.auto_approve:
                request.group_owner = group_owner
                request.community_owner = community.first_owner
                request.privilege = PrivilegeCodes.VIEW
                request.redeemed = True
                request.approved = True
                request.when_responded = timezone.now()
                request.save()
                approved = True
                request.community_owner.uaccess.share_community_with_group(
                    request.community, request.group, request.privilege)
                message = "Request auto-approved to connect group '{}' to community '{}'."\
                    .format(group.name, community.name)

            elif not created:  # refresh request: this has the side effect of disabling any denials
                request.group_owner = group_owner
                request.privilege = None
                request.redeemed = False
                request.approved = False
                request.when_requested = timezone.now()
                request.when_responded = None
                request.save()
                message = "Request updated: connect group '{}' to community '{}'."\
                    .format(group.name, community.name)

            # normal completion
            return message, approved
        else:
            raise PermissionDenied("requester owns neither group nor community.")

    def cancel(self, requester):
        '''
        Cancel a Group/Community request.

        Arguments:
        :param self: request in question
        :param requester: owner of the group or community

        Return value: This returns a triple:
        * message: a message to give to the requester
        * success: whether the action was taken successfully.

        Theory of operation: Either owner can cancel a request.
        '''
        if self.redeemed:
            message = "Connection request between community '{}' and group '{}': "\
                      "already acted upon."\
                      .format(self.community.name, self.group.name)
            return message, False
        if (self.group_owner is not None and requester == self.group_owner) or \
           (self.community_owner is not None and requester == self.community_owner):
            self.delete()
            message = "Connection request between community '{}' and group '{}' cancelled."\
                      .format(self.community.name, self.group.name)
            return message, True
        else:
            message = "Connection request between community '{}' and group '{}': "\
                      "insufficient privilege to cancel request."\
                      .format(self.community.name, self.group.name)
            return message, False

    @classmethod
    def pending(cls, responder=None):
        '''
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests he/she can approve.
        '''
        requests = cls.objects.filter(redeemed=False)
        if responder is not None:
            assert (isinstance(responder, User))
            requests = requests.filter(Q(group_owner__isnull=True,
                                         group__g2ugp__user=responder,
                                         group__g2ugp__privilege=PrivilegeCodes.OWNER)
                                       | Q(community_owner__isnull=True,
                                           community__c2ucp__user=responder,
                                           community__c2ucp__privilege=PrivilegeCodes.OWNER))
        return requests

    @classmethod
    def queued(cls, requester=None):
        '''
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests he/she can cancel.
        '''
        requests = cls.objects.filter(redeemed=False)
        if requester is not None:
            assert (isinstance(requester, User))
            requests = requests.filter(Q(group__g2ugp__user=requester,
                                         group__g2ugp__privilege=PrivilegeCodes.OWNER)
                                       | Q(community__c2ucp__user=requester,
                                           community__c2ucp__privilege=PrivilegeCodes.OWNER))
        return requests

    @classmethod
    def get_request(cls, **kwargs):
        '''
        Returns the unique request, if any, concerning a Group/Community pair.

        Arguments
        :community: the Community object
        :group: the Group object

        This either returns a single object or None if there is none.
        '''
        if __debug__:
            assert ('group' in kwargs)
            assert ('community' in kwargs)

        group = kwargs['group']
        community = kwargs['community']

        try:
            return GroupCommunityRequest.objects.get(group=group, community=community)
        except GroupCommunityRequest.DoesNotExist:
            return None

    def approve(self, responder, privilege=PrivilegeCodes.VIEW):
        ''' approve a request as the owner of the other side of the transaction '''
        assert (isinstance(responder, User))
        if self.redeemed:
            message = "Request is completed and cannot be approved."
            return message, False
        if self.community_owner is None:
            if responder.uaccess.owns_community(self.community):
                self.community_owner = responder
                self.privilege = privilege
                self.redeemed = True
                self.approved = True
                self.when_responded = timezone.now()
                self.save()
                self.community_owner.uaccess.share_community_with_group(
                    self.community, self.group, self.privilege)
                message = "Request to connect group '{}' to community '{}' approved."\
                    .format(self.group.name, self.community.name)
                return message, True
            else:
                message = "You do not own the community and cannot approve this request."
                return message, False
        else:  # if self.group_owner is None:
            if responder.uaccess.owns_group(self.group):
                self.group_owner = responder
                self.redeemed = True
                self.approved = True
                self.when_responded = timezone.now()
                self.save()
                message = "Request to connect group '{}' to community '{}' approved."\
                    .format(self.group.name, self.community.name)
                self.community_owner.uaccess.share_community_with_group(
                    self.community, self.group, self.privilege)
                return message, True
            else:
                message = "You do not own the group and cannot approve this request."
                return message, False

    def decline(self, responder):
        ''' decline a request, as the owner of the other side of the transaction '''
        assert (isinstance(responder, User))
        if self.redeemed:
            message = "Request is completed and cannot be declined."
            return message, False
        if self.community_owner is None:
            if responder.uaccess.owns_community(self.community):
                self.community_owner = responder
                self.privilege = PrivilegeCodes.VIEW
                self.redeemed = True
                self.approved = False
                self.when_responded = timezone.now()
                self.save()
                message = "Request to connect group '{}' to community '{}' declined."\
                    .format(self.group.name, self.community.name)
                return message, True
            else:
                message = "You do not own the community and cannot decline this request."
                return message, False
        else:  # if self.group_owner is None:
            if responder.uaccess.owns_group(self.group):
                self.group_owner = responder
                self.redeemed = True
                self.approved = False
                self.when_responded = timezone.now()
                self.save()
                message = "Request to connect group '{}' to community '{}' declined."\
                    .format(self.group.name, self.community.name)
                return message, True
            else:
                message = "You do not own the group and cannot decline this request."
                return message, False

    @classmethod
    def remove(cls, requester, **kwargs):
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
            assert ('group' in kwargs)
            assert (isinstance(kwargs['group'], Group))
            assert (kwargs['group'].gaccess.active)
            assert ('community_owner' in kwargs)
            assert (isinstance(kwargs['community_owner'], User))
            assert (kwargs['community_owner'].is_active)
            assert ('community' in kwargs)
            assert (isinstance(kwargs['community'], Community))

        group = kwargs['group']
        community = kwargs['community']

        # don't allow anything unless the requester is authorized
        if not requester.owns_community(community):
            message = "User {} does not own community '{}'"\
                .format(requester.username, community.name)
            return message, False

        # delete request from provenance chain
        try:
            request = GroupCommunityRequest.get_request(community=community, group=group)
            request.delete()
        except cls.DoesNotExist:
            pass

        # check whether the group is already not in the community (!)
        if group not in community.member_groups:
            message = "Group '{}' is not in community '{}'."\
                .format(group.name, community.name)
            return message, True

        requester.uaccess_unshare_community_with_group(community, group)
        message = "Group '{}' removed from community '{}'."\
            .format(group.name, community.name)
        return message, True

# TODO: we need some kind of user feedback about what happened when something is denied.
# TODO: it would be nice to know why something's declined.
# TODO: to avoid request storms, the decline should be sticky unless overridden by an invite.
