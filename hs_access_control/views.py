from django.views.generic import TemplateView
from django.contrib.auth.models import User, Group
from hs_access_control.models import Community, GroupCommunityRequest
import logging


logger = logging.getLogger(__name__)


class GroupView(TemplateView):
    template_name = 'hs_access_control/group.html'

    def hydroshare_denied(request, uid, gid, cid=None):
        try:
            user = User.objects.get(id=uid)  # becomes request.user
            # # when in production:
            # user = request.user
            # if not user.is_authenticated:
            #     message = "You must be logged in to access this function."
            #     return message
        except User.DoesNotExist:
            message = "user id {} not found".format(uid)
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

    def get_context_data(request, uid, gid, *args, **kwargs):
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
        denied = request.hydroshare_denied(uid, gid, cid=cid)
        logger.debug("denied is {}".format(denied))
        if denied == "":
            user = User.objects.get(id=uid)
            group = Group.objects.get(id=gid)
            if 'action' in kwargs:
                community = Community.objects.get(id=cid)
                if action == 'approve':
                    gcr = GroupCommunityRequest.objects.get(
                        group=group, community=community)
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

                elif action == 'retract':  # remove a pending request
                    gcr = GroupCommunityRequest.objects.get(
                        community=community, group=group)
                    message, worked = GroupCommunityRequest.remove(
                        requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'leave':
                    user.uaccess.unshare_community_with_group(
                        this_community=community,
                        this_group=group)
                    gcr = GroupCommunityRequest.objects.get(
                        community=community, group=group)
                    gcr.delete()
                    message = "group {} ({}) removed from community {} ({}). "\
                        .format(group.name, group.id, community.name, community.id)
                    logger.debug(message)

                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            context['denied'] = denied  # empty string means ok
            context['message'] = message
            context['user'] = user
            context['group'] = group
            context['uid'] = uid
            context['gid'] = gid
            context['debug'] = GroupCommunityRequest.objects.all()

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
                .exclude(c2gcp__group=group)

            return context

        else:  # non-empty denied means an error.
            context['denied'] = denied
            logger.debug("denied is '{}'".format(denied))
            return context


class CommunityView(TemplateView):
    template_name = 'hs_access_control/community.html'

    def hydroshare_denied(request, uid, cid, gid=None):
        try:
            user = User.objects.get(id=uid)  # becomes request.user
            # # when in production:
            # user = request.user
            # if not user.is_authenticated:
            #     message = "You must be logged in to access this function."
            #     return message
        except User.DoesNotExist:
            message = "user id {} not found".format(uid)
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

    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        uid = int(uid)
        cid = int(cid)
        if 'gid' in kwargs:
            gid = int(kwargs['gid'])
        else:
            gid = None
        if 'action' in kwargs:
            action = kwargs['action']
        else:
            action = None
        logger.debug("uid={} cid={} action={} gid={}".format(uid, cid, action, gid))
        denied = request.hydroshare_denied(uid, cid, gid)
        logger.debug("denied is {}".format(denied))
        if denied == "":
            user = User.objects.get(id=int(uid))
            community = Community.objects.get(id=int(cid))
            if action is not None:
                group = Group.objects.get(id=int(gid))
                if action == 'approve':  # approve a request from a group
                    gcr = GroupCommunityRequest.objects.get(
                        community__id=int(cid),
                        group__id=int(kwargs['gid'])
                    )
                    message, worked = gcr.approve(responder=User.objects.get(id=int(uid)))
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

                elif action == 'retract':  # remove a pending request
                    gcr = GroupCommunityRequest.objects.get(community=community, group=group)
                    message, worked = GroupCommunityRequest.remove(
                         requester=user, group=group, community=community)
                    logger.debug("message = '{}' worked='{}'".format(message, worked))

                elif action == 'remove':  # remove a group from this community
                    user.uaccess.unshare_community_with_group(
                        this_community=community,
                        this_group=group)
                    gcr = GroupCommunityRequest.objects.filter(community__id=int(cid),
                                                               group__id=int(kwargs['gid']))
                    if gcr.count() > 0:
                        gcr = gcr[0]
                        gcr.delete()

                    message = "group {} ({}) removed from community {} ({}). "\
                        .format(group.name, group.id, community.name, community.id)
                    logger.debug(message)
                else:
                    message = "unknown action '{}'".format(action)
                    logger.error(message)

            context['uid'] = uid
            context['cid'] = cid
            context['denied'] = denied
            context['message'] = message
            context['community'] = Community.objects.get(id=int(cid))

            # groups that can be invited are those that are not already invited or members.
            context['groups'] = Group.objects.filter(gaccess__active=True)\
                .exclude(invite_g2gcr__community=context['community'])\
                .exclude(g2gcp__community=context['community']).order_by('name')

            context['pending'] = GroupCommunityRequest.objects.filter(
                community=Community.objects.get(id=int(cid)),
                redeemed=False, group_owner__isnull=True)

            # debugging
            context['debug'] = GroupCommunityRequest.objects.all()

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

    def get_context_data(request, uid, cid, *args, **kwargs):
        context = {}
        context['uid'] = uid
        context['cid'] = cid
        return context


class TestGroup(TemplateView):
    template_name = 'hs_access_control/group_test.html'

    def get_context_data(request, uid, gid, *args, **kwargs):
        context = {}
        context['uid'] = uid
        context['gid'] = gid
        return context
