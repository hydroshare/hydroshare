from django.views.generic import View
from django.contrib.auth.models import User, Group
from django.db.models import F
from django.http import JsonResponse
from datetime import datetime

from hs_access_control.models import Community, CommunityRequest, \
    GroupCommunityRequest, PrivilegeCodes

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
            picture_url = cr.picture.url
        except ValueError:
            picture_url = ""
        return {
            'id': cr.id,
            'type': 'CommunityRequest',
            'name': cr.name,
            'url': cr.url,
            'email': cr.email,
            'description': cr.description or '',
            'purpose': cr.purpose or '',
            'auto_approve': 1 if cr.auto_approve is True else 0,
            'date_requested': (cr.date_requested.strftime("%m/%d/%Y, %H:%M:%S")
                               if cr.date_requested is not None
                               else ""),
            'date_processed': (cr.date_processed.strftime("%m/%d/%Y, %H:%M:%S")
                               if cr.date_processed is not None
                               else ""),
            'picture_url': picture_url,
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

    """ Request the creation of a community. """

    def hydroshare_denied(self):
        user = self.request.user
        if not user or not user.is_authenticated:
            message = "You must be logged in to access this function."
            logger.error(message)
            return message
        else:
            return ""

    def post(self, *args, **kwargs):
        message = ''
        denied = ''
        context = {}

        if 'action' in kwargs:  # what to do; otherwise provide options
            action = kwargs['action']
        else:
            action = None

        if 'crid' in kwargs:  # which entry to act upon, if any
            crid = int(kwargs['crid'])
        else:
            crid = None

        cr = None  # no request yet

        denied = self.hydroshare_denied()

        if denied == "":  # no error; permission granted
            user = self.request.user
            if action is not None:
                if crid is not None:  # request
                    try:
                        cr = CommunityRequest.objects.get(id=int(crid))
                        if cr.approved is not None:
                            denied = "Request already acted upon!"
                    except CommunityRequest.DoesNotExist:
                        denied = "No request matching that id found"
                if denied == "":
                    if action == 'request' or action == 'approve' or action == "decline":
                        # update the community description from POST data.
                        name = self.request.POST['name']
                        description = self.request.POST['description']
                        email = self.request.POST['email']
                        url = self.request.POST['url']
                        purpose = self.request.POST['purpose']
                        # picture = self.request.POST['picture']
                        closed = self.request.POST['closed']
                        owner = self.request.POST['owner']
                        if user.username != 'admin' and owner != user.username:
                            denied = "You are only allowed to specify yourself as owner"
                        else:
                            try:
                                ouser = User.objects.get(username=owner)
                            except User.DoesNotExist:
                                denied = "No owner '{}'".format(owner)
                        if denied == "":
                            if cr is not None:
                                cr.name = name
                                cr.description = description
                                cr.email = email
                                cr.purpose = purpose
                                cr.url = url
                                # cr.picture = picture
                                cr.closed = closed
                                cr.owner = User.objects.get(username=ouser)
                                cr.date_requested = datetime.now()
                                cr.save()
                            else:  # create request
                                cr = CommunityRequest.objects.create(
                                    name=name,
                                    description=description,
                                    email=email,
                                    purpose=purpose,
                                    url=url,
                                    # picture=picture,
                                    closed=closed,
                                    owner=ouser)
                        if action == 'approve':
                            if user.username == 'admin':
                                message = cr.approve()
                            else:
                                denied = "You are not allowed to approve community requests."
                        elif action == 'decline':  # decline a request to create a community
                            if user.username == 'admin':
                                message = cr.decline()
                            else:
                                denied = "You are not allowed to decline community requests"
                    elif action == 'remove':
                        if user == cr.owner or user.username == 'admin':
                            cr.delete()
                            message = "Request removed"
                        else:
                            denied = "You are not allowed to remove this request"
                    else:
                        denied = "unknown action '{}'".format(action)
                        logger.error(denied)

        # at the end of this, message is not None
        # if one tried to act on the request;
        # otherwise denied indicates what went wrong.

        if denied == "":
            # build a JSON object that contains the results of the query
            context = {}
            context['denied'] = denied
            context['message'] = message
            context['user'] = user_json(user)
            if cr is not None:
                context['request'] = cr_json(cr)

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

            return JsonResponse(context)

        else:
            context = {}
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=404)
