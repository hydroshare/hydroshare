from django.views.generic import TemplateView
from django.contrib.auth.models import User, Group
from hs_access_control.models import Community, GroupCommunityRequest
import logging


logger = logging.getLogger(__name__)


class GroupApprovalView(TemplateView):
    template_name = 'hs_access_control/group_approval.html'

    def hydroshare_permissions(request, uid, gid, cid=None):
        try:
            user = User.objects.get(id=uid)
            ## when in production:
            # user = request.user
            # if not user.is_authenticated: 
            #     message = "You must be logged in to access this function." 
            #     return message
            group = Group.objects.get(id=gid)
            if user.uaccess.owns_group(group):
                if cid is None:
                    return ""
                else:
                    community = Community.objects.get(id=cid)
                    gcr = GroupCommunityRequest.objects.filter(group=group, community=community, redeemed=False)
                    if gcr.count() < 1:
                        message = "no request for user {} ({}), group {} ({}), and community {} ({})"\
                                  .format(user.username, user.id, group.name, group.id, community.name, community.id)
                        logger.error(message)
                        return message
                    else:
                        return ""

            else:
                message = "user {} ({}) does not own group {} ({})"\
                          .format(user.username, user.id, group.name, group.id)
                logger.error(message)
                return message
        except Exception as e:
            message = "invalid user id {} or group id {}".format(uid, gid)
            logger.error("{}: exception {}".format(message, e))
            return message

    def get_context_data(request, uid, gid, *args, **kwargs):
        context = {}
        message = ''
        if 'cid' in kwargs:
            cid = kwargs['cid']
        else:
            cid = None
        status = request.hydroshare_permissions(uid, gid, cid=cid)
        if status == "":
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
                    message = "unknown action '{}'".format(kwargs['action'])
                    logger.error(message)
            context['status'] = status  # empty string = ok
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
        else:  # non-empty status means an error.
            context['status'] = status
            return context


class GroupRequestView(TemplateView):
    template_name = 'hs_access_control/group_request.html'

    def hydroshare_permissions(request, uid, gid, cid=None):
        try:
            user = User.objects.get(id=uid)
            ## when in production:
            # user = request.user
            # if not user.is_authenticated: 
            #     message = "You must be logged in to access this function." 
            #     return message
            group = Group.objects.get(id=gid)
            if user.uaccess.owns_group(group):
                return ""
            else:
                message = "user {} ({}) does not own group {} ({})"\
                          .format(user.username, user.id, group.name, group.id)
                logger.error(message)
                return message
        except Exception as e:
            message = "invalid user id {} or group id {}".format(uid, gid)
            logger.error("{}: exception {}".format(message, e))
            return message

    def get_context_data(request, uid, gid, *args, **kwargs):
        message = ''
        context = {}
        if 'cid' in kwargs:
            cid = kwargs['cid']
        else:
            cid = None
        status = request.hydroshare_permissions(uid, gid, cid=cid)
        if status == "":
            if 'action' in kwargs:
                if kwargs['action'] == 'request':
                    message, worked = GroupCommunityRequest.create_or_update(
                        group=Group.objects.get(id=int(gid),
                        community=Community.objects.get(id=int(cid)),
                        requester=User.objects.get(id=int(uid)))
                else:
                    message = "unknown action '{}'".format(kwargs['action'])
                    logger.error(message)

            context['status'] = status
            context['message'] = message
            context['uid'] = uid
            context['gid'] = gid
            context['group'] = Group.objects.get(id=int(gid))
            context['communities'] = Group.objects.filter()\
                .exclude(invite_c2gcr__community=context['community'])\
                .exclude(g2gcp__community=context['community'])
            return context
        else:
            context['status'] = status
            return context

class CommunityApprovalView(TemplateView):
    template_name = 'hs_access_control/community_approval.html'

    def hydroshare_permissions(request, uid, cid, gid=None):
        try:
            user = User.objects.get(id=uid)  # becomes request.user
            ## when in production:
            # user = request.user
            # if not user.is_authenticated: 
            #     message = "You must be logged in to access this function." 
            #     return message
            community = Community.objects.get(id=gid)
            if user.uaccess.owns_community(community):
                if gid is None:
                    return ""
                else:
                    group = Group.objects.get(id=gid)
                    gcr = GroupCommunityRequest.objects.filter(group=group, community=community, redeemed=False)
                    if gcr.count() < 1:
                        message = "no request for user {} ({}), group {} ({}), and community {} ({})"\
                                  .format(user.username, user.id, group.name, group.id, community.name, community.id)
                        logger.error(message)
                        return message
                    else:
                        return ""

            else:
                message = "user {} ({}) does not own group {} ({})"\
                          .format(user.username, user.id, group.name, group.id)
                logger.error(message)
                return message
        except Exception as e:
            message = "invalid user id {} or group id {}".format(uid, gid)
            logger.error("{}: exception {}".format(message, e))
            return message

    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        if 'gid' in kwargs:
            gid = kwargs['gid']
        else:
            gid = None
        status = request.hydroshare_permissions(uid, gid, cid)
        if status == "":
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
                    message = "unknown action '{}'".format(kwargs['action'])
                    logger.error(message)
            context['status'] = status
            context['message'] = message
            context['community'] = Community.objects.get(id=int(cid))
            context['gcr'] = GroupCommunityRequest.objects.filter(
                community=Community.objects.get(id=int(cid)),
                group__gaccess__active=True,
                community_owner__isnull=True,
                redeemed=False)
            return context
        else:  # non-empty status means an error.
            context['status'] = status
            return context


class CommunityInviteView(TemplateView):
    template_name = 'hs_access_control/community_invite.html'

    def hydroshare_permissions(request, uid, cid, gid=None):
        try:
            user = User.objects.get(id=uid)  
            ## when in production:
            # user = request.user
            # if not user.is_authenticated: 
            #     message = "You must be logged in to access this function." 
            #     return message
                
            community = Community.objects.get(id=cid)
            if user.uaccess.owns_community(community):
                return ""
            else:
                message = "user {} ({}) does not own community {} ({})"\
                          .format(user.username, user.id, community.name, community.id)
                logger.error(message)
                return message
        except Exception as e:
            message = "invalid user id {} or community id {}".format(uid, cid)
            logger.error("{}: exception {}".format(message, e))
            return message

    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        if 'gid' in kwargs:
            gid = kwargs['gid']
        else:
            gid = None
        status = request.hydroshare_permissions(uid, cid, gid=gid)
        if status == "":
            if 'action' in kwargs:
                if kwargs['action'] == 'invite':
                    message, worked = GroupCommunityRequest.create_or_update(
                        group=Group.objects.get(id=int(kwargs['gid'])),
                        community=Community.objects.get(id=int(cid)),
                        requester=User.objects.get(id=int(uid)))
                else:
                    message = "unknown action '{}'".format(kwargs['action'])
                    logger.error(message)

            context['status'] = status
            context['message'] = message
            context['uid'] = uid
            context['cid'] = cid
            context['community'] = Community.objects.get(id=int(cid))
            context['groups'] = Group.objects.filter(gaccess__active=True)\
                .exclude(invite_g2gcr__community=context['community'])\
                .exclude(g2gcp__community=context['community'])
            return context
        else:
            context['status'] = status
            return context


class TestCommunityApproval(TemplateView):
    template_name = 'hs_access_control/community_approval_test.html'

    def get_context_data(request, uid, cid, *args, **kwargs):
        context = {}
        context['uid'] = uid
        context['cid'] = cid
        return context


class TestCommunityInvite(TemplateView):
    template_name = 'hs_access_control/community_invite_test.html'

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
