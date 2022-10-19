import logging

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import JsonResponse
from django.views.generic import View
from rest_framework import status

from hs_access_control.models import Community, GroupCommunityRequest, PrivilegeCodes
from hs_access_control.models.community import RequestCommunity

logger = logging.getLogger(__name__)


def user_json(user):
    """ JSON format for user data suitable for UI """
    if user is not None:
        return {
            'type': 'User',
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
    else:
        return {}


def group_json(group):
    """ JSON format for group data suitable for UI """
    if group is not None:
        try:
            url = group.gaccess.picture.url
        except ValueError:
            url = ""
        return {
            'id': group.id,
            'type': 'Group',
            'name': group.name,
            'active': 1 if group.gaccess.active is True else 0,
            'discoverable': 1 if group.gaccess.discoverable is True else 0,
            'public': 1 if group.gaccess.public is True else 0,
            'shareable': 1 if group.gaccess.shareable is True else 0,
            'auto_approve': 1 if group.gaccess.auto_approve is True else 0,
            'requires_explanation': 1 if group.gaccess.requires_explanation is True else 0,
            'purpose': group.gaccess.purpose or '',
            'description': group.gaccess.description or '',
            'email': group.gaccess.email or '',
            'date_created': group.gaccess.date_created.strftime("%m/%d/%Y, %H:%M:%S"),
            'picture': url or '',
            'owners': [user_json(u) for u in group.gaccess.owners]
        }
    else:
        return {}


def community_json(community):
    """ JSON format for community data suitable for UI """
    if community is not None:
        try:
            url = community.picture.url
        except ValueError:
            url = ""
        return {
            'id': community.id,
            'type': 'Community',
            'name': community.name,
            'url': community.url or '',
            'email': community.email or '',
            'description': community.description or '',
            'purpose': community.purpose or '',
            'auto_approve_resource': 1 if community.auto_approve_resource is True else 0,
            'auto_approve_group': 1 if community.auto_approve_group is True else 0,
            'date_created': community.date_created.strftime("%m/%d/%Y, %H:%M:%S"),
            'picture': url or '',
            'closed': 1 if community.closed is True else 0,
            'owners': [user_json(u) for u in community.owners]
        }
    else:
        return {}

def pending_community_request_json(pending_request):
    """ JSON format for pending community creation request data suitable for UI """
    if pending_request is not None:
        return {
            'requested_by': user_json(pending_request.requested_by),
            'community_to_approve': community_json(pending_request.community_to_approve),
            'date_requested': pending_request.date_requested.strftime("%m/%d/%Y, %H:%M:%S"),
            'date_processed': 0 if pending_request.approved is None else pending_request.date_processed.strftime("%m/%d/%Y, %H:%M:%S"), 
            'approved': 1 if pending_request.approved is True else 0,
        }
    else:
        return {}


def gcr_json(request):
    """ JSON format for request data suitable for UI """
    return {
        'type': 'GroupCommunityRequest',
        'group': group_json(request.group),
        'community': community_json(request.community),
        'group_owner': user_json(request.group_owner),
        'community_owner': user_json(request.community_owner),
        'when_community': (request.when_community.strftime("%m/%d/%Y, %H:%M:%S")
                           if request.when_community is not None
                           else ""),
        'when_group': (request.when_group.strftime("%m/%d/%Y, %H:%M:%S")
                       if request.when_group is not None
                       else ""),
        'privilege': request.privilege,
        'redeemed': 1 if request.redeemed is True else 0,
    }


def cr_json(cr):
    """ JSON format for community request data suitable for UI """
    if cr is not None:
        community = cr.community_to_approve
        try:
            picture_url = community.picture.url
        except ValueError:
            picture_url = ""
        try:
            banner_url = community.banner.url
        except ValueError:
            banner_url = ""

        return {
            'id': cr.id,
            'type': 'CommunityRequest',
            'name': community.name,
            'url': community.url,
            'email': community.email,
            'description': community.description or '',
            'purpose': community.purpose or '',
            'auto_approve_resource': community.auto_approve_resource,
            'auto_approve_group': community.auto_approve_group,
            'date_requested': cr.date_requested,
            'date_processed': cr.date_processed,
            'picture_url': picture_url,
            'banner_url': banner_url,
            'closed': community.closed,
            'owner': user_json(cr.requested_by)
        }
    else:
        return {}


class GroupView(View):
    """ Group transaction engine manages joining and leaving communities """

    def hydroshare_denied(self, gid, cid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            return message

        try:
            group = Group.objects.get(id=gid)
        except Group.DoesNotExist:
            message = "group id {} not found".format(gid)
            return message

        if user.uaccess.owns_group(group):
            if cid is None:
                return ""
            else:
                community = Community.objects.filter(id=cid)
                if community.count() < 1:
                    message = "community id {} not found".format(cid)
                    return message
                else:
                    return ""

        else:
            message = "user '{}' does not own group '{}'"\
                      .format(user.username, group.name)
            return message

    def get(self, *args, **kwargs):
        context = {}
        message = ''

        if 'gid' in kwargs:
            gid = kwargs['gid']
        else:
            gid = None

        if 'cid' in kwargs:
            cid = kwargs['cid']
        else:
            cid = None

        if 'action' in kwargs:
            action = kwargs['action']
        else:
            action = None

        denied = self.hydroshare_denied(gid, cid=cid)
        if denied == "":
            user = self.request.user
            group = Group.objects.get(id=gid)
            if 'action' in kwargs:
                community = Community.objects.get(id=cid)
                if action == 'approve':
                    gcr = GroupCommunityRequest.objects.get(
                        group=group, community=community)
                    if gcr.redeemed:  # reset to unredeemed in order to approve
                        gcr.reset(responder=user)
                    message, worked = gcr.approve(responder=user)

                elif action == 'decline':  # decline an invitation from a community
                    gcr = GroupCommunityRequest.objects.get(
                        group=group, community=community)
                    message, worked = gcr.decline(responder=user)
                    logger.debug(message)

                elif action == 'join':  # request to join a community
                    message, worked = GroupCommunityRequest.create_or_update(
                        group=group, community=community, requester=user)

                elif action == 'leave':  # leave a community
                    message, worked = GroupCommunityRequest.remove(
                        requester=user, group=group, community=community)

                elif action == 'retract':  # remove a pending request
                    message, worked = GroupCommunityRequest.retract(
                        requester=user, group=group, community=community)

                else:
                    denied = "unknown action '{}'".format(action)

            # build a JSON object that contains the results of the query
            if denied == "":
                context = {}

                context['denied'] = denied  # empty string means ok
                context['message'] = message
                context['user'] = user_json(user)
                context['group'] = group_json(group)

                # communities joined
                context['joined'] = []
                for c in Community.objects.filter(c2gcp__group=group).order_by('name'):
                    context['joined'].append(community_json(c))

                # invites from communities to be approved or eclined
                context['approvals'] = []
                for r in GroupCommunityRequest.objects.filter(
                        group=group,
                        group__gaccess__active=True,
                        group_owner__isnull=True).order_by('community__name'):
                    context['approvals'].append(gcr_json(r))

                # pending requests from this group
                context['pending'] = []
                for r in GroupCommunityRequest.objects.filter(
                        group=group, redeemed=False, community_owner__isnull=True)\
                        .order_by('community__name'):
                    context['pending'].append(gcr_json(r))

                # Communities that can be joined.
                context['available_to_join'] = []
                for c in Community.objects.filter().exclude(invite_c2gcr__group=group)\
                                                   .exclude(c2gcp__group=group)\
                                                   .order_by('name'):
                    context['available_to_join'].append(community_json(c))

                # requests that were declined by others
                context['they_declined'] = []
                for r in GroupCommunityRequest.objects.filter(
                        group=group, redeemed=True, approved=False,
                        when_group__lt=F('when_community')).order_by('community__name'):
                    context['they_declined'].append(gcr_json(r))

                # requests that were declined by us
                context['we_declined'] = []
                for r in GroupCommunityRequest.objects.filter(
                        group=group, redeemed=True, approved=False,
                        when_group__gt=F('when_community')).order_by('community__name'):
                    context['we_declined'].append(gcr_json(r))

                return JsonResponse(context)
            else:
                context = {}
                context['denied'] = denied
                logger.error(denied)
                return JsonResponse(context, status=404)

        else:  # non-empty denied means an error.
            context = {}
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=404)


class CommunityView(View):
    """ Community transaction engine manages inviting and approving groups """

    def hydroshare_denied(self, cid, gid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            return message

        try:
            community = Community.objects.get(id=cid)
        except Community.DoesNotExist:
            message = "community id {} not found".format(cid)
            return message

        if user.uaccess.owns_community(community):
            if gid is None:
                return ""
            else:
                group = Group.objects.filter(id=gid)
                if group.count() < 1:
                    message = "group id {} not found".format(gid)
                    return message
                else:
                    return ""

        else:
            message = "user '{}' does not own community '{}'"\
                      .format(user.username, community.name)
            return message

    def get(self, *args, **kwargs):
        message = ''
        context = {}

        if 'cid' in kwargs:
            cid = int(kwargs['cid'])
        else:
            cid = None

        if 'gid' in kwargs:
            gid = int(kwargs['gid'])
        else:
            gid = None

        if 'action' in kwargs:
            action = kwargs['action']
        else:
            action = None

        if 'uid' in kwargs:
            uid = kwargs['uid']
        else:
            uid = None

        if 'addrem' in kwargs:
            addrem = kwargs['addrem']
        else:
            addrem = None

        denied = self.hydroshare_denied(cid, gid)
        if denied == "":
            # these are needed for every request
            user = self.request.user
            community = Community.objects.get(id=int(cid))
            if action == 'approve':  # approve a request from a group
                group = Group.objects.get(id=int(gid))
                gcr = GroupCommunityRequest.objects.get(
                    community=community, group=group)
                if gcr.redeemed:  # make it possible to approve a formerly declined request
                    gcr.reset(responder=user)
                message, worked = gcr.approve(responder=user)

            elif action == 'decline':  # decline a request from a group
                group = Group.objects.get(id=int(gid))
                gcr = GroupCommunityRequest.objects.get(
                    community__id=int(cid),
                    group__id=int(kwargs['gid']))
                message, worked = gcr.decline(responder=user)

            elif action == 'invite':
                group = Group.objects.get(id=int(gid))
                try:
                    message, worked = GroupCommunityRequest.create_or_update(
                        requester=user, group=group, community=community)
                except Exception as e:
                    logger.debug(e)

            elif action == 'remove':  # remove a group from this community
                group = Group.objects.get(id=int(gid))
                message, worked = GroupCommunityRequest.remove(
                    requester=user, group=group, community=community)

            elif action == 'retract':  # remove a pending request
                group = Group.objects.get(id=int(gid))
                message, worked = GroupCommunityRequest.retract(
                     requester=user, group=group, community=community)

            elif action == 'deactivate':  # deactivate a community
                group = Group.objects.get(id=int(gid))
                community.active = False
                community.save()
                context = {'denied': ''}  # community is gone now
                return JsonResponse(context)

            elif action == 'owner':  # add or remove an owner.
                # look up proposed user id
                try:
                    newuser = User.objects.get(username=uid)
                    if addrem == 'add':
                        if not newuser.uaccess.owns_community(community):
                            user.uaccess.share_community_with_user(
                                community, newuser, PrivilegeCodes.OWNER)
                        else:
                            denied = "user '{}' already owns community".format(uid)
                    elif addrem == 'remove':
                        if not newuser.uaccess.owns_community(community):
                            denied = "user '{}' does not own community".format(uid)
                        elif community.owners.count() == 1:
                            denied = "Cannot remove last owner '{}' of community".format(uid)
                        else:
                            user.uaccess.unshare_community_with_user(
                                community, newuser)
                    else:
                        denied = "unknown user action {}".format(addrem)
                except User.DoesNotExist:
                    denied = "user id '{}' does not exist.".format(uid)

            elif action is not None:
                denied = "unknown action '{}'".format(action)

            if denied == '':
                # build a JSON object that contains the results of the query
                context = {}

                context['denied'] = denied
                context['message'] = message
                context['user'] = user_json(user)
                context['community'] = community_json(community)

                # groups that can be invited are those that are not already invited or members.
                context['groups'] = []
                for g in Group.objects.filter(gaccess__active=True)\
                                      .exclude(invite_g2gcr__community=community)\
                                      .exclude(g2gcp__community=community)\
                                      .order_by('name'):
                    context['groups'].append(group_json(g))

                context['pending'] = []
                for r in GroupCommunityRequest.objects.filter(
                        community=community, redeemed=False, group_owner__isnull=True).order_by('group__name'):
                    context['pending'].append(gcr_json(r))

                # requests that were declined by us
                context['we_declined'] = []
                for r in GroupCommunityRequest.objects.filter(
                        community=community, redeemed=True, approved=False,
                        when_group__lt=F('when_community')).order_by('group__name'):
                    context['we_declined'].append(gcr_json(r))

                # requests that were declined by others
                context['they_declined'] = []
                for r in GroupCommunityRequest.objects.filter(
                        community=community, redeemed=True, approved=False,
                        when_group__gt=F('when_community')).order_by('group__name'):
                    context['they_declined'].append(gcr_json(r))

                # group requests to be approved
                context['approvals'] = []
                for r in GroupCommunityRequest.objects.filter(
                        community=Community.objects.get(id=int(cid)),
                        group__gaccess__active=True,
                        community_owner__isnull=True,
                        redeemed=False).order_by('group__name'):
                    context['approvals'].append(gcr_json(r))

                # group members of community
                context['members'] = []
                for g in Group.objects.filter(g2gcp__community=community).order_by('name'):
                    context['members'].append(group_json(g))

                return JsonResponse(context)
            else:  # non-empty denied means an error.
                context = {}
                context['denied'] = denied
                logger.error(denied)
                return JsonResponse(context, status=404)
        else:  # non-empty denied means an error.
            context = {}
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=404)


class CommunityRequestView(View):

    """ View for creating or acting on a pending request to create a community. """

    def hydroshare_denied(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this functionality."
            logger.error(message)
            return message
        else:
            return ""

    def get_community_requests(self, user, context=None):
        if context is None:
            context = {}
        # approved requests
        if user.is_superuser:  # privileged user sees all
            context['approved'] = []
            for r in RequestCommunity.objects.filter(approved=True):
                context['approved'].append(cr_json(r))

            # declined requests
            context['declined'] = []
            for r in RequestCommunity.objects.filter(approved=False):
                context['declined'].append(cr_json(r))

            # pending requests
            context['pending'] = []
            for r in RequestCommunity.objects.filter(approved__isnull=True):
                context['pending'].append(cr_json(r))

        else:  # just for current user
            context['approved'] = []
            for r in RequestCommunity.objects.filter(approved=True, requested_by=user):
                context['approved'].append(cr_json(r))

            # declined requests
            context['declined'] = []
            for r in RequestCommunity.objects.filter(approved=False, requested_by=user):
                context['declined'].append(cr_json(r))

            # pending requests
            context['pending'] = []
            for r in RequestCommunity.objects.filter(approved__isnull=True, requested_by=user):
                context['pending'].append(cr_json(r))

        return JsonResponse(context)

    def get(self, *args, **kwargs):
        user = self.request.user
        denied = self.hydroshare_denied()
        context = {}
        if denied:
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=status.HTTP_401_UNAUTHORIZED)

        return self.get_community_requests(user)

    def post(self, *args, **kwargs):
        message = ''
        cr = None  # no community request yet
        user = self.request.user
        denied = self.hydroshare_denied()
        context = {}
        if denied:
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=status.HTTP_401_UNAUTHORIZED)

        action = kwargs['action']
        crid = kwargs.get('crid', '')
        if not crid:
            if action != 'request':
                denied = "Invalid action requested for community request"
            else:
                try:
                    cr = RequestCommunity.create_request(self.request)
                except ValidationError as err:
                    denied = err.message
        else:
            # user taking action on an existing community request
            crid = int(crid)
            action = kwargs['action']
            if action not in ('update', 'approve', 'decline', 'remove'):
                denied = "Invalid action requested for community request"

            if not denied:
                try:
                    cr = RequestCommunity.objects.get(id=crid)
                    if cr.approved is not None:
                        denied = "Request already acted upon!"
                except RequestCommunity.DoesNotExist:
                    denied = "No request matching that id found"

            if not denied:
                if action == 'update':
                    # update the community fields from POST data.
                    cr_by_user = cr.requested_by
                    if cr_by_user != user and not user.is_superuser:
                        denied = "You are not allowed to update this community request"
                    if not denied:
                        try:
                            cr.update_request(user, self.request)
                        except ValidationError as err:
                            denied = err.message
                elif action == 'approve':
                    if user.is_superuser:
                        cr.approve()
                        message = "Request approved"
                    else:
                        denied = "You are not allowed to approve community requests."
                elif action == 'decline':  # decline a request to create a community
                    if user.is_superuser:
                        cr.decline()
                        message = "Request declined"
                    else:
                        denied = "You are not allowed to decline community requests"
                else:
                    # action == 'remove'
                    if user == cr.requested_by or user.is_superuser:
                        cr.remove()
                        message = "Request removed"
                    else:
                        denied = "You are not allowed to remove this request"

        # at the end of this, message is not None
        # if one tried to act on the request;
        # otherwise denied indicates what went wrong.
        if denied:
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)

        # build a JSON object that contains the results of the query
        context['denied'] = denied
        context['message'] = message
        context['user'] = user_json(user)
        context['request'] = cr_json(cr)

        return self.get_community_requests(user, context)
