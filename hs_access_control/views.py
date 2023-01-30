import logging

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db.models import F
from django.http import JsonResponse
from django.views.generic import View
from hs_core.templatetags.hydroshare_tags import best_name
from rest_framework import status

from hs_access_control.models import Community, GroupCommunityRequest, PrivilegeCodes
from hs_access_control.models.community import RequestCommunity
from .emails import CommunityGroupEmailNotification, CommunityRequestEmailNotification
from .enums import CommunityActions, CommunityGroupEvents, CommunityRequestActions, CommunityRequestEvents

logger = logging.getLogger(__name__)


def user_json(user):
    """ JSON format for user data suitable for UI """
    if user is not None:
        user.viewable_contributions = user.uaccess.can_view_resources_owned_by(user)

        picture = None
        if user.userprofile.picture:
            picture = user.userprofile.picture.url

        return {
            "id": user.id,
            "pictureUrl": picture or "",
            "best_name": best_name(user),
            "user_name": user.username,
            # Data used to populate profile badge:
            "email": user.email,
            "organization": user.userprofile.organization or '',
            "title": user.userprofile.title or '',
            "contributions": len(user.uaccess.owned_resources) if user.is_active else None,
            "viewable_contributions": user.viewable_contributions if user.is_active else None,
            "subject_areas": user.userprofile.subject_areas or '',
            "identifiers": user.userprofile.identifiers,
            "state": user.userprofile.state,
            "country": user.userprofile.country,
            "joined": user.date_joined.strftime("%d %b, %Y"),
            "is_active": 1 if user.is_active else 0
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
            'name': community.name or '',
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
        'privilege': request.privilege or "",
        'redeemed': 1 if request.redeemed is True else 0,
    }


def cr_json(cr):
    """ JSON format for community request data suitable for UI """
    if cr is not None:
        return {
            'id': cr.id,
            'requested_by': user_json(cr.requested_by),
            'community_to_approve': community_json(cr.community_to_approve),
            'date_requested': cr.date_requested.strftime("%m/%d/%Y, %H:%M:%S"),
            'date_processed': 0 if cr.pending_approval else cr.date_processed.strftime("%m/%d/%Y, %H:%M:%S"),
            'status': 'Approved' if cr.approved is True else 'Submitted' if cr.pending_approval is True else 'Rejected',
            'decline_reason': cr.decline_reason if cr.decline_reason is not None else '',
        }
    else:
        return {}


def error_response(err_message):
    context = {'denied': err_message}
    logger.error(err_message)
    return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


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

    def validate_request_parameters(self, kwargs):
        action = kwargs.get('action', None)
        req_params = {}
        err_msg = ''
        allowed_actions = [action.value for action in CommunityActions if action not in
                           (CommunityActions.OWNER, CommunityActions.ADD, CommunityActions.INVITE,
                            CommunityActions.DEACTIVATE)]
        if action is not None and action not in allowed_actions:
            err_msg = "unknown action for community: '{}'".format(action)
            return err_msg, req_params

        if action is not None:
            req_params['action'] = action
        cid = kwargs.get('cid', None)
        if action is not None and cid is None:
            err_msg = "id for the community is missing"
            return err_msg, req_params

        if cid is not None:
            cid = int(cid)
            req_params['cid'] = cid

        gid = kwargs.get('gid', None)
        if gid is None:
            err_msg = "id for the group is not provided"
            return err_msg, req_params

        gid = int(gid)
        req_params['gid'] = gid

        return err_msg, req_params

    def post(self, *args, **kwargs):
        message = ''
        validation_err_msg, req_params = self.validate_request_parameters(kwargs)
        if validation_err_msg:
            return error_response(validation_err_msg)

        cid = req_params.get('cid', None)
        gid = req_params['gid']
        action = req_params.get('action', None)

        denied = self.hydroshare_denied(gid, cid=cid)
        if denied:
            return error_response(denied)

        group = Group.objects.get(id=gid)
        user = self.request.user

        if action is not None:
            community = Community.objects.get(id=cid)
            if action == CommunityActions.APPROVE:
                # group owner accepting an invitation for a group to join a community
                gcr = GroupCommunityRequest.get_request(group=group, community=community)
                if gcr.redeemed:  # reset to unredeemed in order to approve
                    gcr.reset(responder=user)
                message, worked = gcr.approve(responder=user)
                if not worked:
                    denied = message
                else:
                    # email notify to concerned parties
                    CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                    on_event=CommunityGroupEvents.APPROVED).send()

            elif action == CommunityActions.DECLINE:  # decline an invitation from a community
                # group owner declining an invitation for a group to join a community
                gcr = GroupCommunityRequest.objects.get(
                    group=group, community=community)
                message, worked = gcr.decline(responder=user)
                if not worked:
                    denied = message
                else:
                    # email notify to concerned parties
                    CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                    on_event=CommunityGroupEvents.DECLINED).send()

            elif action == CommunityActions.JOIN:  # request to join a community
                # group owner making a request to join a community
                message, worked = GroupCommunityRequest.create_or_update(
                    group=group, community=community, requester=user)
                # send email to group owner
                gcr = GroupCommunityRequest.get_request(community=community, group=group)
                # email notify to community owners
                CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                on_event=CommunityGroupEvents.JOIN_REQUESTED).send()

            elif action == CommunityActions.LEAVE:  # leave a community
                # group owner making a group leave a community
                message, worked = GroupCommunityRequest.remove(
                    requester=user, group=group, community=community)
                if not worked:
                    denied = message

            else:
                assert action == CommunityActions.RETRACT
                # remove a pending request
                message, worked = GroupCommunityRequest.retract(
                    requester=user, group=group, community=community)
                if not worked:
                    denied = message

        # build a JSON object that contains the results of the query
        context = {}
        if denied:
            return error_response(denied)

        context['denied'] = denied  # empty string means ok
        context['message'] = message
        context['user'] = user_json(user)
        context['group'] = group_json(group)
        return JsonResponse(context)

    def get(self, *args, **kwargs):
        gid = kwargs['gid']
        denied = self.hydroshare_denied(gid)
        if denied:
            return error_response(denied)

        group = Group.objects.get(id=gid)
        user = self.request.user
        context = {}
        context['denied'] = denied  # empty string means ok
        context['user'] = user_json(user)
        context['group'] = group_json(group)

        # communities joined
        context['joined'] = []
        for c in Community.objects.filter(c2gcp__group=group).order_by('name'):
            context['joined'].append(community_json(c))

        # invites from communities to be approved or declined
        context['approvals'] = []
        for r in GroupCommunityRequest.objects.filter(
                group=group,
                group__gaccess__active=True,
                group_owner__isnull=True).order_by('community__name'):
            context['approvals'].append(gcr_json(r))

        # pending requests from this group
        context['pending'] = []
        for r in GroupCommunityRequest.objects.filter(
                group=group, redeemed=False, community_owner__isnull=True) \
                .order_by('community__name'):
            context['pending'].append(gcr_json(r))

        # Communities that can be joined.
        context['available_to_join'] = []
        for c in Community.objects.filter().exclude(invite_c2gcr__group=group) \
                .exclude(c2gcp__group=group) \
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


class CommunityView(View):
    """ Community transaction engine manages inviting and approving groups """

    def hydroshare_denied(self, cid, gid=None):
        user = self.request.user
        no_error = ""
        if not user or not user.is_authenticated:
            err_message = "You must be logged in to access this function."
            return err_message

        try:
            community = Community.objects.get(id=cid)
        except Community.DoesNotExist:
            err_message = "community id {} not found".format(cid)
            return err_message

        if user.uaccess.owns_community(community):
            if gid is None:
                return no_error
            else:
                try:
                    Group.objects.get(id=gid)
                except Group.DoesNotExist:
                    err_message = "group id {} not found".format(gid)
                    return err_message
                return no_error
        else:
            err_message = "user '{}' does not own community '{}'" \
                .format(user.username, community.name)
            return err_message

    def validate_request_parameters(self, kwargs):
        action = kwargs.get('action', None)
        req_params = {}
        err_msg = ''
        allowed_actions = [action.value for action in CommunityActions if action
                           not in (CommunityActions.JOIN, CommunityActions.LEAVE)]
        if action is not None and action not in allowed_actions:
            err_msg = "unknown action for community: '{}'".format(action)
            return err_msg, req_params

        if action is not None:
            req_params['action'] = action
        cid = kwargs.get('cid', None)
        if cid is None:
            err_msg = "id for the community is not provided"
            return err_msg, req_params
        else:
            cid = int(cid)
        req_params['cid'] = cid

        gid = kwargs.get('gid', None)
        if gid is None and action != CommunityActions.OWNER and action is not None:
            err_msg = "id for the group is not provided"
            return err_msg, req_params

        if gid is not None:
            gid = int(gid)
            req_params['gid'] = gid

        uid = kwargs.get('uid', None)
        if uid is None and action == CommunityActions.OWNER and action is not None:
            err_msg = "id for the community owner is not provided"
            return err_msg, req_params
        req_params['uid'] = uid

        addrem = kwargs.get('addrem', None)
        if addrem is None and action == CommunityActions.OWNER:
            err_msg = "action related to ownership of the community is not provided"
            return err_msg, req_params
        if addrem is not None and addrem not in (CommunityActions.ADD.value, CommunityActions.REMOVE.value):
            err_msg = "provided action is not a valid action related to ownership of the community"
            return err_msg, req_params

        if addrem is not None:
            req_params['addrem'] = addrem

        return err_msg, req_params

    def get_pending_requests(self, community):
        pending = []
        for r in GroupCommunityRequest.objects.filter(
                community=community, redeemed=False, group_owner__isnull=True).order_by('group__name'):
            pending.append(gcr_json(r))
        return pending
    
    def get_groups(self, community):
        groups = []
        for g in Group.objects.filter(gaccess__active=True)\
                              .exclude(invite_g2gcr__community=community)\
                              .exclude(g2gcp__community=community)\
                              .order_by('name'):
            groups.append(group_json(g))
        return groups
    
    def get_group_members(self, community):
        members = []
        for g in Group.objects.filter(g2gcp__community=community).order_by('name'):
            members.append(group_json(g))

        return members

    def get(self, *args, **kwargs):
        message = ''
        cid = kwargs.get('cid', None)
        denied = self.hydroshare_denied(cid)
        if denied:
            return error_response(denied)

        # user and community are needed for every request
        user = self.request.user
        community = Community.objects.get(id=cid)

        # build a JSON object that contains the results of the query
        context = {}
        context['denied'] = denied
        context['message'] = message
        context['user'] = user_json(user)
        context['community'] = community_json(community)

        # groups that can be invited are those that are not already invited or members.
        context['groups'] = self.get_groups(community)

        context['pending'] = self.get_pending_requests(community)

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

    def post(self, *args, **kwargs):
        message = ""
        validation_err_msg, req_params = self.validate_request_parameters(kwargs)
        if validation_err_msg:
            return error_response(validation_err_msg)

        cid = req_params['cid']
        gid = req_params.get('gid', None)
        uid = req_params.get('uid', None)
        action = req_params.get('action', None)
        addrem = req_params.get('addrem', None)

        denied = self.hydroshare_denied(cid, gid)
        if denied:
            return error_response(denied)

        # user and community are needed for every request
        user = self.request.user
        community = Community.objects.get(id=cid)
        if action == CommunityActions.DEACTIVATE:  # deactivate a community
            community.active = False
            community.save()
            context = {'denied': ''}  # community is gone now
            return JsonResponse(context)

        if action == CommunityActions.APPROVE:  # approve a request from a group
            group = Group.objects.get(id=gid)
            gcr = GroupCommunityRequest.objects.get(community=community, group=group)
            if gcr.redeemed:  # make it possible to approve a formerly declined request
                gcr.reset(responder=user)
            message, worked = gcr.approve(responder=user)
            if not worked:
                denied = message
            else:
                # send email to group owners
                CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                on_event=CommunityGroupEvents.APPROVED).send()
                #TODO: return data needed to update UI
        elif action == CommunityActions.DECLINE:  # decline a request from a group
            group = Group.objects.get(id=gid)
            gcr = GroupCommunityRequest.get_request(community=community, group=group)
            message, worked = gcr.decline(responder=user)
            if not worked:
                denied = message
            else:
                # send email to group owners
                CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                on_event=CommunityGroupEvents.DECLINED).send()

        elif action == CommunityActions.INVITE:
            group = Group.objects.get(id=gid)
            try:
                message, approved = GroupCommunityRequest.create_or_update(
                    requester=user, group=group, community=community)
                # send email to group owner
                gcr = GroupCommunityRequest.get_request(community=community, group=group)
                CommunityGroupEmailNotification(request=self.request, group_community_request=gcr,
                                                on_event=CommunityGroupEvents.INVITED).send()
                context = {}
                if approved:
                    context['members'] = self.get_group_members(community)
                context['pending'] = self.get_pending_requests(community)
                return JsonResponse(context)
            except Exception as e:
                logger.error(str(e))
                denied = str(e)
        elif action == CommunityActions.REMOVE:  # remove a group from this community
            group = Group.objects.get(id=gid)
            message, worked = GroupCommunityRequest.remove(
                requester=user, group=group, community=community)
            if not worked:
                denied = message
            else:
                context = { 
                    'members': self.get_group_members(community),
                    'groups': self.get_groups(community)
                }
                return JsonResponse(context)
        elif action == CommunityActions.RETRACT:  # remove a pending request
            group = Group.objects.get(id=gid)
            message, worked = GroupCommunityRequest.retract(
                requester=user, group=group, community=community)
            if not worked:
                denied = message
            else:
                context = { 
                    'pending': self.get_pending_requests(community),
                    'groups': self.get_groups(community)
                }
                return JsonResponse(context)
        elif action == CommunityActions.OWNER:  # add or remove an owner.
            # look up proposed user id
            try:
                newuser = User.objects.get(id=uid)
                if addrem == CommunityActions.ADD:
                    if not newuser.uaccess.owns_community(community):
                        user.uaccess.share_community_with_user(
                            community, newuser, PrivilegeCodes.OWNER)
                    else:
                        denied = "user '{}' already owns community".format(uid)
                elif addrem == CommunityActions.REMOVE:
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

        if denied:
            return error_response(denied)
        # build a JSON object that contains the results of the query
        context = {}
        context['denied'] = denied
        context['message'] = message
        context['user'] = user_json(user)
        context['community'] = community_json(community)
        return JsonResponse(context)


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

    def validate_request_parameters(self, kwargs):
        action = kwargs.get('action', None)
        req_params = {}
        err_msg = ''
        allowed_actions = [action.value for action in CommunityRequestActions]
        if action is not None and action not in allowed_actions:
            err_msg = "unknown action for community: '{}'".format(action)
            return err_msg, req_params

        if action is not None:
            req_params['action'] = action

        crid = kwargs.get('crid', None)
        if crid is None and action != CommunityRequestActions.REQUEST:
            err_msg = "id for the community request is not provided"
            return err_msg, req_params

        if crid is not None:
            crid = int(crid)
            try:
                RequestCommunity.objects.get(id=crid)
            except RequestCommunity.DoesNotExist:
                err_msg = f"No existing request to create a new community was found for the id:{crid}"
                return err_msg, req_params
            if action == CommunityRequestActions.REQUEST:
                err_msg = "Invalid action"
                return err_msg, req_params

            req_params['crid'] = crid

        return err_msg, req_params

    def get_community_requests(self, user, context=None):
        if context is None:
            context = {}

        context['approved'] = []
        context['declined'] = []
        context['pending'] = []

        # privileged (super user) user sees all

        # approved requests
        approved_qs = RequestCommunity.objects.filter(pending_approval=False, declined=False)

        # declined requests
        declined_qs = RequestCommunity.objects.filter(declined=True)

        # pending requests
        pending_qs = RequestCommunity.objects.filter(pending_approval=True)

        if not user.is_superuser:  # just for current user
            # approved requests
            approved_qs = approved_qs.filter(requested_by=user)

            # declined requests
            declined_qs = declined_qs.filter(requested_by=user)

            # pending requests
            pending_qs = pending_qs.filter(requested_by=user)

        for a_cr in approved_qs:
            context['approved'].append(cr_json(a_cr))

        for d_cr in declined_qs:
            context['declined'].append(cr_json(d_cr))

        for p_cr in pending_qs:
            context['pending'].append(cr_json(p_cr))

        return JsonResponse(context)

    def get(self, *args, **kwargs):
        """gets a list of community requests created by given user. If the use is an admin, all community requests
        are returned
        """
        user = self.request.user
        denied = self.hydroshare_denied()
        context = {}
        if denied:
            context['denied'] = denied
            logger.error(denied)
            return JsonResponse(context, status=status.HTTP_401_UNAUTHORIZED)

        return self.get_community_requests(user)

    def post(self, *args, **kwargs):
        """creates a community request or takes a specified action (decline, approve, or delete) on an
        existing community request - request to create a new community
        """
        message = ''
        validation_err_msg, req_params = self.validate_request_parameters(kwargs)
        if validation_err_msg:
            return error_response(validation_err_msg)

        crid = req_params.get('crid', None)
        action = req_params.get('action', None)
        denied = self.hydroshare_denied()
        if denied:
            return error_response(denied)

        user = self.request.user

        if action == CommunityRequestActions.REQUEST:
            # user is making a request for a new community
            try:
                cr = RequestCommunity.create_request(self.request)
            except ValidationError as err:
                denied = err.message
            else:
                # send email to hydroshare support/help
                CommunityRequestEmailNotification(request=self.request, community_request=cr,
                                                  on_event=CommunityRequestEvents.CREATED).send()
        else:
            # user taking action on an existing community request - request to create a new community
            cr = RequestCommunity.objects.get(id=crid)
            if action == CommunityRequestActions.UPDATE:
                # update the community fields from POST data.
                cr_by_user = cr.requested_by
                if cr_by_user != user and not user.is_superuser:
                    denied = "You are not allowed to update this community request"
                if not denied:
                    try:
                        cr.update_request(user, self.request)
                    except ValidationError as err:
                        denied = err.message
            elif action == CommunityRequestActions.APPROVE:
                if user.is_superuser:
                    cr.approve()
                    message = "Request approved"
                    # send email to the user who requested the new community
                    CommunityRequestEmailNotification(request=self.request, community_request=cr,
                                                      on_event=CommunityRequestEvents.APPROVED).send()

                else:
                    denied = "You are not allowed to approve community requests."
            elif action == CommunityRequestActions.DECLINE:  # decline a request to create a community
                decline_reason = self.request.POST.get('reason', '')
                decline_reason = decline_reason.strip()
                if not decline_reason:
                    denied = "Reason for declining community request must be provided"
                elif user.is_superuser:
                    cr.decline(reason=decline_reason)
                    message = "Request declined"
                    # send email to the user who requested the new community
                    CommunityRequestEmailNotification(request=self.request, community_request=cr,
                                                      on_event=CommunityRequestEvents.DECLINED).send()
                else:
                    denied = "You are not allowed to decline community requests"
            elif action == CommunityRequestActions.RESUBMIT: # resubmit a request after it has been declined
                cr.resubmit()
                message = "Request has been resubmitted"
                CommunityRequestEmailNotification(request=self.request, community_request=cr,
                                                  on_event=CommunityRequestEvents.RESUBMITTED).send()
            else:
                assert action == CommunityRequestActions.REMOVE
                if user == cr.requested_by or user.is_superuser:
                    cr.remove()
                    message = "Request removed"
                else:
                    denied = "You are not allowed to remove this request"

        # at the end of this, message is not None
        # if one tried to act on the request;
        # otherwise denied indicates what went wrong.
        context = {}
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
