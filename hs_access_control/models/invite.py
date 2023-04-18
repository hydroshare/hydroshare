from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from hs_access_control.enums import CommunityActions, CommunityJoinRequestTypes
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
    """
    A mechanism for handling Invitations from a community owner to a group owner.
    * The community owner creates a GroupCommunityRequest.
    * The group owner uses GroupCommunityRequest.act() to respond.
    """

    # target
    group = models.ForeignKey(Group, on_delete=models.CASCADE, editable=False, null=False, related_name='invite_g2gcr')
    # source
    community = models.ForeignKey(Community, on_delete=models.CASCADE, editable=False, null=False,
                                  related_name='invite_c2gcr')
    # invitee - this is set only if a group owner asks to join a community
    group_owner = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, null=True, default=None,
                                    related_name='invite_go2gcr')
    # inviter - this is set only if a community owner invites a group to join
    community_owner = models.ForeignKey(User, on_delete=models.CASCADE, editable=False, null=True,
                                        related_name='invite_co2gcr')

    # when group action was taken
    when_group = models.DateTimeField(editable=False, null=True, default=None)

    # when community action was taken
    when_community = models.DateTimeField(editable=False, null=True, default=None)

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
        """
        On save, update timestamps.
        See discussion of auto_now and auto_now_add in stack overflow for details
        """

        if not self.id:  # when created
            if self.group_owner:
                self.when_group = timezone.now()
            else:
                self.when_community = timezone.now()
        return super(GroupCommunityRequest, self).save(*args, **kwargs)

    @property
    def group_absolute_url(self):
        from hs_core.hydroshare import current_site_url
        site_domain = current_site_url()
        url = f"{site_domain}/group/{self.group.id}"
        return url

    @property
    def community_absolute_url(self):
        from hs_core.hydroshare import current_site_url
        site_domain = current_site_url()
        url = f"{site_domain}/community/{self.community.id}"
        return url

    @classmethod
    def create_or_update(cls, **kwargs):
        """
        Request a group to be included in a community. This can only be done by agreement between
        a community owner and a group owner.

        :param group: target Group.
        :param community: target Community.
        :param requester: a User doing the requesting. Must own the community or the group.

        Usage:
            GroupCommunityRequest.create_or_update(group={X}, community={Y}, requester={Z})

        Return: returns a tuple of values
        * message: a status message for the community owner using this routine.
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

        """

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

        if not group.gaccess.active:
            message = "Group '{}' is not active.".format(group.name)
            raise ValidationError(message)

        # first check whether the group is already in the community (!)
        if group in community.member_groups:
            message = "Group '{}' is already connected to community '{}'."\
                .format(group.name, community.name)
            raise ValidationError(message)

        if community.closed:
            message = "Community '{}' is currently not allowing more groups to join.".format(community.name)
            raise ValidationError(message)

        # requester owns both community and group
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
            request.when_group = timezone.now()
            request.when_community = timezone.now()
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
            # requester owns community (this must be an invite)
            community_owner = requester

            if group not in community_owner.uaccess.my_groups and not group.gaccess.public \
                    and not group.gaccess.discoverable:
                raise PermissionDenied("You must be a member of a private group to invite it to a community.")

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
                request.when_community = timezone.now()
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
                request.group_owner = None
                request.privilege = privilege
                request.redeemed = False
                request.approved = False
                request.when_community = timezone.now()
                request.when_group = None
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

            # auto-approve if there's already a pending invite(!)
            if not request.redeemed and request.community_owner is not None and request.privilege is not None:
                request.group_owner = group_owner
                request.redeemed = True
                request.approved = True
                request.when_group = timezone.now()
                request.save()
                approved = True
                request.community_owner.uaccess.share_community_with_group(
                    request.community, request.group, request.privilege)
                message = "Request approved to connect group '{}' to community '{}'"\
                    " because there is a matching request."\
                    .format(group.name, community.name)

            # auto-approve if auto_approve is True
            elif community.auto_approve_group:
                request.group_owner = group_owner
                request.community_owner = community.first_owner
                request.privilege = PrivilegeCodes.VIEW
                request.redeemed = True
                request.approved = True
                request.when_group = timezone.now()
                request.when_community = timezone.now()
                request.save()
                approved = True
                request.community_owner.uaccess.share_community_with_group(
                    request.community, request.group, request.privilege)
                message = "Request auto-approved to connect group '{}' to community '{}'."\
                    .format(group.name, community.name)

            elif not created:  # refresh request: this has the side effect of disabling any denials
                request.group_owner = group_owner
                request.community_owner = None
                request.privilege = None
                request.redeemed = False
                request.approved = False
                request.when_group = timezone.now()
                request.when_community = None
                request.save()
                message = "Request updated: connect group '{}' to community '{}'."\
                    .format(group.name, community.name)

            # normal completion
            return message, approved
        else:
            raise PermissionDenied("requester owns neither group nor community.")

    def cancel(self, requester):
        """
        Cancel a Group/Community request.

        Arguments:
        :param self: request in question
        :param requester: owner of the group or community

        Return value: This returns a triple:
        * message: a message to give to the requester
        * success: whether the action was taken successfully.

        Theory of operation: Either owner can cancel a request.
        """

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
        """
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests he/she can approve.
        """
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
        """
        Return a list of active requests as class objects. These can be further filtered
        to determine whether the current user has any requests he/she can cancel.
        """
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
        """
        Returns the unique request, if any, concerning a Group/Community pair.

        Arguments
        :community: the Community object
        :group: the Group object

        This either returns a single object or None if there is none.
        """

        if __debug__:
            assert ('group' in kwargs)
            assert ('community' in kwargs)

        group = kwargs['group']
        community = kwargs['community']

        try:
            return GroupCommunityRequest.objects.get(group=group, community=community)
        except GroupCommunityRequest.DoesNotExist:
            return None

    def reset(self, responder):
        """ make a completed request approvable again """
        if not self.redeemed:
            message = "One can only reset a redeemed request."
            return message, False
        elif responder.uaccess.owns_community(self.community):
            self.community_owner = None
            self.when_community = None
            self.approved = False
            self.redeemed = False
        elif responder.uaccess.owns_group(self.group):
            self.group_owner = None
            self.when_group = None
            self.approved = False
            self.redeemed = False

        self.save()

    def approve_request(self, responder):
        """ approve a request as the owner of the community receiving the request to join """

        return self._act_on_group_community_request(user=responder,
                                                    request_type=CommunityJoinRequestTypes.GROUP_REQUESTING,
                                                    action_type=CommunityActions.APPROVE)

    def accept_invitation(self, responder):
        """ approve a request as the owner of the group being invited """

        return self._act_on_group_community_request(user=responder,
                                                    request_type=CommunityJoinRequestTypes.COMMUNITY_INVITING,
                                                    action_type=CommunityActions.APPROVE)

    def decline_invitation(self, responder):
        """ decline a request, as an owner of the group being invited """
        return self._act_on_group_community_request(user=responder,
                                                    request_type=CommunityJoinRequestTypes.COMMUNITY_INVITING,
                                                    action_type=CommunityActions.DECLINE)

    def decline_group_request(self, responder):
        """decline a request, as the owner of the community"""

        return self._act_on_group_community_request(user=responder,
                                                    request_type=CommunityJoinRequestTypes.GROUP_REQUESTING,
                                                    action_type=CommunityActions.DECLINE)

    def _act_on_group_community_request(self, user, request_type, action_type):
        """helper method to support acting on request related to group joining a community"""

        assert isinstance(user, User)
        assert request_type in (CommunityJoinRequestTypes.GROUP_REQUESTING,
                                CommunityJoinRequestTypes.COMMUNITY_INVITING)
        assert action_type in (CommunityActions.APPROVE, CommunityActions.DECLINE)

        if self.redeemed:
            message = f"Request is completed and cannot be {action_type.value}d."
            return message, False

        if request_type == CommunityJoinRequestTypes.GROUP_REQUESTING:
            if not user.uaccess.owns_community(self.community):
                message = f"You do not own the community and cannot {action_type.value} this request."
                return message, False
            else:
                self.privilege = PrivilegeCodes.VIEW
                self.when_community = timezone.now()
        elif not user.uaccess.owns_group(self.group):   # community invited group to join
            message = f"You do not own the group and cannot {action_type.value} this request."
            return message, False
        else:
            self.when_group = timezone.now()

        self.redeemed = True
        self.approved = action_type == CommunityActions.APPROVE
        self.save()
        if action_type == CommunityActions.APPROVE:
            self.user = user
            if request_type == CommunityJoinRequestTypes.GROUP_REQUESTING:
                # user is the community owner approving the request
                self.user = user
            else:
                self.user = self.community_owner

            self.user.uaccess.share_community_with_group(
                self.community, self.group, self.privilege)

        message = f"Request to connect group '{self.group.name}' to " \
                  f"community '{self.community.name}' {action_type.value}d."

        return message, True

    @classmethod
    def remove(cls, requester, **kwargs):
        """
        Remove a group from a community. This can only be done by a community or group owner.
        :param group: target group.
        :param community: target community.

        Usage:
            GroupCommunityPrivilege.remove(group={X}, community={Y}, community_owner={Z})

        Return values: returns a pair of values
        * message: a status message for the user.
        * success: whether the removal succeeded.
        """

        if __debug__:
            assert ('group' in kwargs)
            assert (isinstance(kwargs['group'], Group))
            assert (kwargs['group'].gaccess.active)
            assert ('community' in kwargs)
            assert (isinstance(kwargs['community'], Community))

        group = kwargs['group']
        community = kwargs['community']

        # don't allow anything unless the requester is authorized
        if not requester.uaccess.owns_community(community) and\
                not requester.uaccess.owns_group(group):
            message = "User {} does not own community '{}' or group '{}'"\
                .format(requester.username, community.name, group.name)
            return message, False

        # delete request from provenance chain
        try:
            request = GroupCommunityRequest.get_request(community=community, group=group)
            if request is not None:
                request.delete()
        except cls.DoesNotExist:
            pass

        # check whether the group is already not in the community (!)
        if group not in community.member_groups:
            message = "Group '{}' is not in community '{}'."\
                .format(group.name, community.name)
            return message, True

        try:
            requester.uaccess.unshare_community_with_group(community, group)
        except:     # noqa
            return 'Failed to remove Group from Community', False
        message = "Group '{}' removed from community '{}'."\
            .format(group.name, community.name)
        return message, True

    @classmethod
    def retract(cls, requester, **kwargs):
        """
        Retract an unredeemed request. This can only be done by a community or group owner.
        :param group: target group.
        :param community: target community.

        Usage:
            GroupCommunityPrivilege.retract(group={X}, community={Y}, community_owner={Z})

        Return values: returns a pair of values
        * message: a status message for the user.
        * success: whether the removal succeeded.

        """
        if __debug__:
            assert ('group' in kwargs)
            assert (isinstance(kwargs['group'], Group))
            assert (kwargs['group'].gaccess.active)
            assert ('community' in kwargs)
            assert (isinstance(kwargs['community'], Community))

        group = kwargs['group']
        community = kwargs['community']

        # don't allow anything unless the requester is authorized
        if not requester.uaccess.owns_community(community) and\
                not requester.uaccess.owns_group(group):
            message = "User {} does not own community '{}' or group '{}'"\
                .format(requester.username, community.name, group.name)
            return message, False

        # delete request from provenance chain
        try:
            request = GroupCommunityRequest.get_request(community=community, group=group)
            if request.redeemed:
                message = "Request to put group '{}' into community '{}' already redeemed."\
                    .format(group.name, community.name)
                return message, False
            else:
                request.delete()
                message = "Removed request to put group '{}' into community '{}'"\
                    .format(group.name, community.name)
                return message, True

        except cls.DoesNotExist:
            message = "Request to put group '{}' into community '{}' does not exist."\
                .format(group.name, community.name)
            return message, True


# TODO: we need some kind of user feedback about what happened when something is denied.
# - Email notifications have been put in place for community requests
# TODO: it would be nice to know why something's declined.
# TODO: to avoid request storms, the decline should be sticky unless overridden by an invite.
