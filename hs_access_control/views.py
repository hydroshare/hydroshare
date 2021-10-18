from django.views.generic import TemplateView
from django.contrib.auth.models import User, Group
from hs_access_control.models import Community, GroupCommunityRequest
import logging


logger = logging.getLogger(__name__)


class GroupApprovalView(TemplateView):
    template_name = 'hs_access_control/group_approval.html'

    def get_context_data(request, uid, gid, *args, **kwargs):
        context = {}
        message = ''
        logger.debug("got to get_context_data: uid={} gid={}".format(uid, gid))
        if 'action' in kwargs:
            if kwargs['action'] == 'approve':
                gcr = GroupCommunityRequest.objects.get(
                    group__id=int(gid),
                    community__id=int(kwargs['cid']))
                message, worked = gcr.approve(responder=User.objects.get(id=int(uid)))
            elif kwargs['action'] == 'decline':
                gcr = GroupCommunityRequest.objects.get(
                    group__id=int(gid),
                    community__id=int(kwargs['cid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
            else:
                message = "improper action '{}'".format(kwargs['action'])
                logger.error(message)
        context['message'] = message
        context['group'] = Group.objects.get(id=int(gid))
        context['user'] = User.objects.get(id=int(uid))
        context['uid'] = uid
        context['gid'] = gid
        context['gcr'] = GroupCommunityRequest.objects.filter(
            group__id=int(gid), 
            group__gaccess__active=True, 
            group_owner__isnull=True)
        return context


class CommunityApprovalView(TemplateView):
    template_name = 'hs_access_control/community_approval.html'

    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        if 'action' in kwargs:
            if kwargs['action'] == 'approve':
                gcr = GroupCommunityRequest.objects.get(
                    community__id=int(cid),
                    group__id=int(kwargs['gid'])
                )
                message, worked = gcr.approve(responder=User.objects.get(id=int(uid)))
            elif kwargs['action'] == 'decline':
                gcr = GroupCommunityRequest.objects.get(
                    community__id=int(cid),
                    group__id=int(kwargs['gid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
            else:
                message = "improper action '{}'".format(kwargs['action'])
                logger.error(message)
        context['message'] = message
        context['community'] = Community.objects.get(id=int(cid))
        context['gcr'] = GroupCommunityRequest.objects.filter(
            community=Community.objects.get(id=int(cid)),
            group__gaccess__active=True, 
            community_owner__isnull=True,
            redeemed=False)
        return context


class TestCommunityApproval(TemplateView):
    template_name = 'hs_access_control/community_approval_test.html'

    def get_context_data(request, uid, cid, *args, **kwargs):
        context = {}
        context['uid'] = uid
        context['cid'] = cid
        return context


class TestGroupApproval(TemplateView):
    template_name = 'hs_access_control/group_approval_test.html'

    def get_context_data(request, uid, gid, *args, **kwargs):
        context = {}
        context['uid'] = uid
        context['gid'] = gid
        return context


class DebugView(TemplateView):
    template_name = 'hs_access_control/debug.html'

    def get_context_data(request, *args, **kwargs):
        context = {}
        context['gcall'] = GroupCommunityRequest.objects.all()
        return context
