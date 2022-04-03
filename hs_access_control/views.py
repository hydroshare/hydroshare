from django.views.generic import TemplateView, View
from django.contrib.auth.models import Group
from django.db.models import F
from django.http import HttpResponse
import json

from hs_access_control.models import Community, GroupCommunityRequest
import logging


logger = logging.getLogger(__name__)


class GroupView(TemplateView):
    """ version of the Group transaction engine that returns HTML """
    template_name = 'hs_access_control/group.html'

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

    def get_context_data(self, gid, *args, **kwargs):
        context = {}
        message = ''
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

            context['denied'] = denied  # empty string means ok
            context['message'] = message
            context['user'] = user
            context['group'] = group
            context['gid'] = gid

            # communities joined
            context['joined'] = Community.objects.filter(c2gcp__group=group)

            # invites from communities to be approved or declined
            context['approvals'] = GroupCommunityRequest.objects.filter(
                group=group,
                group__gaccess__active=True,
                group_owner__isnull=True)

            # pending requests from this group
            context['pending'] = GroupCommunityRequest.objects.filter(
                group=group, redeemed=False, community_owner__isnull=True)

            # Communities that can be joined.
            context['communities'] = Community.objects.filter()\
                .exclude(invite_c2gcr__group=group)\
                .exclude(c2gcp__group=group)\
                .exclude(closed=True)

            # requests that were declined by others
            context['they_declined'] = GroupCommunityRequest.objects.filter(
                group=group, redeemed=True, approved=False, when_group__lt=F('when_community'))

            # requests that were declined by us
            context['we_declined'] = GroupCommunityRequest.objects.filter(
                group=group, redeemed=True, approved=False, when_group__gt=F('when_community'))

            return context

        else:  # non-empty denied means an error.
            context['denied'] = denied
            logger.error(denied)
            return context


def user_json(user):
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
    if group is not None: 
        logger.debug('serializing group {}'.format(group.name))
        return {
            'type': 'Group',
            'name': group.name,
            'active': group.gaccess.active,
            'discoverable': group.gaccess.discoverable,
            'public': group.gaccess.public,
            'published': group.gaccess.published,
            'shareable': group.gaccess.shareable,
            'auto_approve': group.gaccess.auto_approve,
            'requires_explanation': group.gaccess.requires_explanation,
            'purpose': group.gaccess.purpose,
            'email': group.gaccess.email,
            'url': group.gaccess.url,
            'date_created': group.gaccess.date_created,
            'picture': group.gaccess.picture.url,
            'owners': [user_json(u) for u in group.owners]
        }
    else: 
        return {}


def community_json(community):
    if community is not None: 
        return {
            'type': 'Community',
            'name': community.name,
            'description': community.description,
            'purpose': community.purpose,
            'auto_approve': community.auto_approve,
            'date_created': community.date_created,
            'picture': community.picture.url,
            'closed': community.closed,
            'owners': [user_json(u) for u in community.owners]
        }
    else: 
        return {}


def gcr_json(request):
    return {
        'type': 'GroupCommunityRequest',
        'group': group_json(request.group),
        'community': community_json(request.community),
        'group_owner': user_json(request.group_owner),
        'community_owner': user_json(request.community_owner),
        'when_community': request.when_community,
        'when_group': request.when_group,
        'privilege': request.privilege,
        'redeemed': request.redeemed
    }


class GroupJsonView(View):
    """ version of the Group transaction engine that returns JSON """

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
            for c in Community.objects.filter(c2gcp__group=group):
                context['joined'].append(community_json(c))

            # invites from communities to be approved or declined
            context['approvals'] = []
            for r in GroupCommunityRequest.objects.filter(
                    group=group,
                    group__gaccess__active=True,
                    group_owner__isnull=True):
                context['approvals'].append(gcr_json(r))

            # pending requests from this group
            context['pending'] = []
            for r in GroupCommunityRequest.objects.filter(
                    group=group, redeemed=False, community_owner__isnull=True):
                context['pending'].append(gcr_json(r))

            # Communities that can be joined.
            context['communities'] = []
            for c in Community.objects.filter().exclude(invite_c2gcr__group=group)\
                                               .exclude(c2gcp__group=group)\
                                               .exclude(closed=True):
                context['communities'].append(community_json(c))

            # requests that were declined by others
            context['they_declined'] = []
            for r in GroupCommunityRequest.objects.filter(
                    group=group, redeemed=True, approved=False,
                    when_group__lt=F('when_community')):
                context['they_declined'].append(gcr_json(r))

            # requests that were declined by us
            context['we_declined'] = []
            for r in GroupCommunityRequest.objects.filter(
                    group=group, redeemed=True, approved=False,
                    when_group__gt=F('when_community')):
                context['we_declined'].append(r)

            return HttpResponse(json.dumps(context), content_type='text/json')

        else:  # non-empty denied means an error.
            context['denied'] = denied
            logger.error(denied)
            return HttpResponse(json.dumps(context), content_type='text/json')


class CommunityView(TemplateView):
    template_name = 'hs_access_control/community.html'

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

    def get_context_data(self, cid, *args, **kwargs):
        message = ''
        context = {}
        cid = int(cid)
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

                elif action == 'remove':  # remove a group from this community
                    message, worked = GroupCommunityRequest.remove(
                         requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                    message = "group {} ({}) removed from community {} ({}). "\
                        .format(group.name, group.id, community.name, community.id)
                    logger.debug(message)
                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            context['cid'] = cid
            context['denied'] = denied
            context['message'] = message
            context['community'] = community

            # groups that can be invited are those that are not already invited or members.
            context['groups'] = Group.objects.filter(gaccess__active=True)\
                .exclude(invite_g2gcr__community=context['community'])\
                .exclude(g2gcp__community=context['community']).order_by('name')

            context['pending'] = GroupCommunityRequest.objects.filter(
                community=community, redeemed=False, group_owner__isnull=True)

            # requests that were declined by us
            context['we_declined'] = GroupCommunityRequest.objects.filter(
                community=community, redeemed=True, approved=False, when_group__lt=F('when_community'))

            # requests that were declined by others
            context['they_declined'] = GroupCommunityRequest.objects.filter(
                community=community, redeemed=True, approved=False, when_group__gt=F('when_community'))

            # group requests to be approved
            context['approvals'] = GroupCommunityRequest.objects.filter(
                community=Community.objects.get(id=int(cid)),
                group__gaccess__active=True,
                community_owner__isnull=True,
                redeemed=False)

            # group members of community
            context['members'] = Group.objects.filter(g2gcp__community=community).order_by('name')

            return context

        else:  # non-empty denied means an error.
            context['denied'] = denied
            return context


class TestCommunity(TemplateView):
    template_name = 'hs_access_control/community_test.html'

    def get_context_data(self, cid, *args, **kwargs):
        context = {}
        context['cid'] = cid
        return context


class TestGroup(TemplateView):
    template_name = 'hs_access_control/group_test.html'

    def get_context_data(self, gid, *args, **kwargs):
        context = {}
        context['gid'] = gid
        return context
