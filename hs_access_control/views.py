from django.views.generic import View
from django.contrib.auth.models import Group
from django.db.models import F
from django.http import HttpResponse
import json

from hs_access_control.models import Community, CommunityRequest, GroupCommunityRequest

import logging
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
            'url': community.url,
            'email': community.email,
            'description': community.description or '',
            'purpose': community.purpose or '',
            'auto_approve': 1 if community.auto_approve is True else 0,
            'date_created': community.date_created.strftime("%m/%d/%Y, %H:%M:%S"),
            'picture': url,
            'closed': 1 if community.closed is True else 0,
            'owners': [user_json(u) for u in community.owners]
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
        try:
            url = cr.picture.url
        except ValueError:
            url = ""
        return {
            'id': cr.id,
            'type': 'CommunityRequest',
            'name': cr.name,
            'url': cr.url,
            'email': cr.email,
            'description': cr.description or '',
            'purpose': cr.purpose or '',
            'auto_approve': 1 if cr.auto_approve is True else 0,
            # 'date_created': cr.date_created.strftime("%m/%d/%Y, %H:%M:%S"),
            'picture': url,
            'closed': 1 if cr.closed is True else 0,
            'owner': user_json(cr.owner)
        }
    else:
        return {}


class GroupView(View):
    """ Group transaction engine manages joining and leaving communities """

    def hydroshare_denied(self, gid, cid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message

        try:
            group = Group.objects.get(id=gid)
        except Group.DoesNotExist:
            message = "group id {} not found".format(gid)
            logger.error(message)
            return message

        if user.uaccess.owns_group(group):
            if cid is None:
                return ""
            else:
                community = Community.objects.filter(id=cid)
                if community.count() < 1:
                    message = "community id {} not found".format(cid)
                    logger.error(message)
                    return message
                else:
                    return ""

        else:
            message = "user {} ({}) does not own group {} ({})"\
                      .format(user.username, user.id, group.name, group.id)
            logger.error(message)
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
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'decline':
                    gcr = GroupCommunityRequest.objects.get(
                        group=group, community=community)
                    message, worked = gcr.decline(responder=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'join':
                    message, worked = GroupCommunityRequest.create_or_update(
                        group=group, community=community, requester=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'leave':
                    message, worked = GroupCommunityRequest.remove(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'retract':  # remove a pending request
                    message, worked = GroupCommunityRequest.retract(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            # build a JSON object that contains the results of the query

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
                context['we_declined'].append(r)

            return HttpResponse(json.dumps(context), content_type='text/json')

        else:  # non-empty denied means an error.
            context['denied'] = denied
            logger.error(denied)
            return HttpResponse(json.dumps(context), content_type='text/json')


class CommunityView(View):
    """ Community transaction engine manages inviting and approving groups """

    def hydroshare_denied(self, cid, gid=None):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message

        try:
            community = Community.objects.get(id=cid)
        except Community.DoesNotExist:
            message = "community id {} not found".format(cid)
            logger.error(message)
            return message

        if user.uaccess.owns_community(community):
            if gid is None:
                return ""
            else:
                group = Group.objects.filter(id=gid)
                if group.count() < 1:
                    message = "group id {} not found".format(gid)
                    logger.error(message)
                    return message
                else:
                    return ""

        else:
            message = "user {} ({}) does not own community {} ({})"\
                      .format(user.username, user.id, community.name, community.id)
            logger.error(message)
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

        logger.debug("cid={} action={} gid={}".format(cid, action, gid))
        denied = self.hydroshare_denied(cid, gid)
        logger.debug("denied is {}".format(denied))
        if denied == "":
            user = self.request.user
            community = Community.objects.get(id=int(cid))
            if action is not None:
                group = Group.objects.get(id=int(gid))
                if action == 'approve':  # approve a request from a group
                    gcr = GroupCommunityRequest.objects.get(
                        community=community, group=group)
                    if gcr.redeemed:  # make it possible to approve a formerly declined request.
                        gcr.reset(responder=user)
                    message, worked = gcr.approve(responder=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'decline':  # decline a request from a group
                    gcr = GroupCommunityRequest.objects.get(
                        community__id=int(cid),
                        group__id=int(kwargs['gid']))
                    message, worked = gcr.decline(responder=user)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'invite':
                    logger.debug("action is invite")
                    try:
                        message, worked = GroupCommunityRequest.create_or_update(
                            requester=user, group=group, community=community)
                        logger.debug("message = '{}' worked='{}'".format(message, worked))
                    except Exception as e:
                        logger.debug(e)

                elif action == 'remove':  # remove a group from this community
                    message, worked = GroupCommunityRequest.remove(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'retract':  # remove a pending request
                    message, worked = GroupCommunityRequest.retract(
                         requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'deactivate':  # deactivate a community
                    community.active = False
                    community.save()
                    return {}  # community is gone now!

                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            # build a JSON object that contains the results of the query

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

            return HttpResponse(json.dumps(context), content_type='text/json')

        else:  # non-empty denied means an error.
            context['denied'] = denied
            logger.error(denied)
            return HttpResponse(json.dumps(context), content_type='text/json')


class CommunityRequestView(View):

    """ Request the creation of a community. """

    def hydroshare_denied(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message


    def get(self, *args, **kwargs):
        message = ''
        context = {}

        if 'crid' in kwargs:
            crid = int(kwargs['crid'])
        else:
            crid = None

        if 'action' in kwargs:
            action = kwargs['action']
        else:
            action = None

        logger.debug("crid={} action={}".format(crid, action))
        denied = self.hydroshare_denied()
        if denied != "":
            context['denied'] = denied
            logger.error(denied)
            return HttpResponse(json.dumps(context), content_type='text/json')

        user = self.request.user
        if action is not None:
            cr = CommunityRequest.objects.get(id=int(crid))
            if action == 'approve':  # approve a request to create a community
                message, worked = cr.approve()
                logger.debug("message = '{}' worked='{}'".format(message, worked))

            elif action == 'decline':  # decline a request to create a community
                cr = CommunityRequest.objects.get(id=int(crid))
                message, worked = cr.decline()
                logger.debug("message = '{}' worked='{}'".format(message, worked))

            else:
                message = "unknown action '{}'".format(action)
                logger.error(message)

        # build a JSON object that contains the results of the query
        context['denied'] = denied
        context['message'] = message
        context['user'] = user_json(user)

        # approved requests
        if user.username == 'admin':  # privileged user sees all
            context['approved'] = []
            for r in CommunityRequest.objects.filter(approved=True):
                context['approved'].append(cr_json(r))

            # declined requests
            context['declined'] = []
            for r in CommunityRequest.objects.filter(approved=False):
                context['declined'].append(cr_json(r))

            # pending requests
            context['pending'] = []
            for r in CommunityRequest.objects.filter(approved__isnull=True):
                context['pending'].append(cr_json(r))

        else:  # just for current user
            context['approved'] = []
            for r in CommunityRequest.objects.filter(approved=True, owner=user):
                context['approved'].append(cr_json(r))

            # declined requests
            context['declined'] = []
            for r in CommunityRequest.objects.filter(approved=False, owner=user):
                context['declined'].append(cr_json(r))

            # pending requests
            context['pending'] = []
            for r in CommunityRequest.objects.filter(approved__isnull=True, owner=user):
                context['pending'].append(cr_json(r))

        return HttpResponse(json.dumps(context), content_type='text/json')
