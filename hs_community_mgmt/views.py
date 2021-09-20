from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, \
    HttpResponseBadRequest, HttpResponseForbidden
import json
# Create your views here.
from django.core import serializers
from django.views.generic import TemplateView
from django.db import models
from django.contrib.auth.models import User, Group
from hs_access_control.models import Community, GroupCommunityRequest,\
                         PrivilegeCodes, GroupMembershipRequest, GroupCommunityPrivilege
# from .models import person

from django.shortcuts import redirect

import logging

logger = logging.getLogger(__name__)

class TestView(TemplateView):
    template_name = 'hs_community_mgmt/test.html'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['people'] = User.objects.all()
        context['teams'] = Group.objects.all()
        # context['over'] = Community.objects.all()
        # context['people'] = serializers.serialize('json', User.objects.all())
        # context['teams'] = serializers.serialize('json', Group.objects.all().values_list('name'))
        # context['over'] = serializers.serialize('json', Community.objects.all())
        context['comms'] = Community.objects.all()
        context['community_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
        context['group_owners'] = User.objects.filter(u2ugp__privilege=PrivilegeCodes.OWNER)
        return context

class UserView(TemplateView):
    template_name = 'hs_community_mgmt/user.html'

    def get_context_data(request, uid, *args, **kwargs):
        u = int(uid)
        user = User.objects.get(id=u)
        context = super().get_context_data(**kwargs)
        context['uinfo'] = {'user': user, 'id' : user.uaccess.id, 'groups' : user.uaccess.my_groups}
        return context

class GroupView(TemplateView):
    template_name = 'hs_community_mgmt/group.html'
    def get_context_data(request, uid, gid, *args, **kwargs):
        context = {}
        message = ''
        user = User.objects.get(id=int(uid))
        if 'action' in kwargs:
            logger.debug("uid={}, gid={}, action={} nuid={}"
                         .format(uid, gid, kwargs['action'], kwargs['nuid']))
            if kwargs['action'] == 'approve':
                gcr = GroupMembershipRequest.objects.get(group=Group.objects.get(id=int(gid)), user__id=int(kwargs['nuid']))
                message, worked  = gcr.approve(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'decline':
                gcr = GroupMembershipRequest.objects.get(group__id=int(gid),
                                                        user__id=int(kwargs['nuid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message 
            elif kwargs['action'] == 'invite_user':
                user = User.objects.get(id=int(kwargs['nuid']))
                ugr = user.uaccess.create_group_membership_request(this_group=Group.objects.get(id=int(gid)), this_user=user)
                context['ugr'] = ugr
        g = int(gid)
        group = Group.objects.get(id=g)
        context['group'] = group
        context['gowners'] = list(group.gaccess.owners)
        context['members'] = group.gaccess.members
        context['size'] = len(group.gaccess.members) 
        context['uid'] = uid
        context['gid'] = gid
        context['requests'] = GroupMembershipRequest.objects.filter(group_to_join=group,
                                                     group_to_join__gaccess__active=True,
                                                     redeemed=False)
        context['all_users'] = User.objects.all()
        context['invitations'] = GroupCommunityRequest.objects.filter(group_id=group).all()
        context['group_owners'] = User.objects.filter(u2ugp__privilege=PrivilegeCodes.OWNER)
        context['community_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
        return context

class CommunityView(TemplateView):
    template_name = 'hs_community_mgmt/comm.html'
    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        context['help'] = "uid={}, cid={}, action={}".format(uid, cid, str(kwargs))
        if 'action' in kwargs: 
            logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
            context['debugging'] = "uid={}, cid={}, gid={},  action={}".format(uid, cid, kwargs['gid'],  kwargs['action']) 
            if kwargs['action'] == 'approve':
                context['check'] = "MADE IT INSIDE APPROVE GCR" 
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid), group__id=int(kwargs['gid']))
                message, worked  = gcr.approve(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'decline': 
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid), 
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'cancel':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.cancel(requester=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'invite_group':
                message, worked = GroupCommunityRequest.create_or_update(group=Group.objects.get(id=int(kwargs['gid'])), \
                                                                         community=Community.objects.get(id=int(cid)), \
                                                                         requester=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'delete':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.remove(requester=User.objects.get(id=int(uid)),\
                                             group=Group.objects.get(id=int(kwargs['gid'])),\
                                             community=Community.objects.get(id=int(cid)),\
                                             community_owner=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = message
            elif kwargs['action'] == 'remove_group':
                user = User.objects.get(id=int(uid))
                if user.uaccess.can_unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                        this_group=Group.objects.get(id=int(kwargs['gid']))):
                        user.uaccess.unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                        this_group=Group.objects.get(id=int(kwargs['gid'])))
            elif kwargs['action'] == 'change_user':
                logger.debug("message = '{}' worked='{}'".format("Work in progress", "<--"))
                context['uid'] = int(uid)
                context['cid'] = int(cid)
                user = User.objects.get(id=int(uid))
                context['community'] = Community.objects.get(id=int(cid))
                context['owned_communities'] = Community.objects.filter(id=int(cid), c2ucp__user=user, c2ucp__privilege=PrivilegeCodes.OWNER)
                context['uinfo'] = {'user': user, 'id' : user.uaccess.id, 'groups' : user.uaccess.my_groups}
                context['comm_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
                context['groups'] = Group.objects.all()
                context['users'] = User.objects.all()
                context['gcr'] = GroupCommunityRequest.objects.filter(community__id=int(cid),
                                         redeemed=False, community__c2ucp__user=user)
                context['gcall'] = GroupCommunityRequest.objects.filter(community__id=int(cid), 
                                                                        community__c2ucp__user=user, community__c2ucp__privilege=PrivilegeCodes.OWNER)
                context['redeemed'] = GroupCommunityRequest.objects.filter(community__id=int(cid), redeemed=True, community__c2ucp__user=user, 
                                                                           community__c2ucp__privilege=PrivilegeCodes.OWNER)
                context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True, approved=False)
                return context    
            else:
                message = "improper action '{}'".format(kwargs['action'])
                logger.error(message)
        context['message'] = message
        context['debug'] = GroupCommunityRequest.objects.all()
        context['uid'] = uid
        context['cid'] = cid
        context['community'] = Community.objects.get(id=int(cid))
        context['comm_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['gcall'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)))
        context['redeemed'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True)
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True, approved=False)
        context['all_groups'] = Group.objects.all()
        return context

class RequestView(TemplateView):
    class Debugging(TemplateView):
        template_name = 'hs_community_mgmt/debugging.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            context = {}
            message = ''
            context['gcall'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)))
            return context

    class Redeemed(TemplateView):
        template_name = 'hs_community_mgmt/redeemed.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            context = {}
            message = ''
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
                if kwargs['action'] == 'delete':
                    gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                    message, worked = gcr.remove(requester=User.objects.get(id=int(uid)),\
                                             group=Group.objects.get(id=int(kwargs['gid'])),\
                                             community=Community.objects.get(id=int(cid)),\
                                             community_owner=User.objects.get(id=int(uid)))
                    context['message'] = message
                    context['worked'] = worked
            context['redeemed'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True)
            return context

    class Requests(TemplateView):
        template_name='hs_community_mgmt/request.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            context = {}
            message = ''
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
                if kwargs['action'] == 'approve':
                    gcr = GroupCommunityRequest.objects.get(community__id=int(cid), group__id=int(kwargs['gid']))
                    message, worked  = gcr.approve(responder=User.objects.get(id=int(uid)))
                    context['message'] = message
                    logger.debug("message = '{}' worked='{}'".format(message, worked))
                elif kwargs['action'] == 'decline':
                    gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                            group__id=int(kwargs['gid']))
                    message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
            context['uid'] = uid
            context['cid'] = cid
            return context
   
    class Invitations(TemplateView):
        template_name='hs_community_mgmt/invitations.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
                if kwargs['action'] == 'cancel':
                    gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                    message, worked = gcr.cancel(requester=User.objects.get(id=int(uid)))
                    logger.debug("message = '{}' worked='{}'".format(message, worked))
            context = {}
            message = ''
            context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
            context['uid'] = uid
            context['cid'] = cid
            return context
 
    class Denied(TemplateView):
        template_name='hs_community_mgmt/denied.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
                if kwargs['action'] == 'delete':
                    gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                    message, worked = gcr.remove(requester=User.objects.get(id=int(uid)),\
                                             group=Group.objects.get(id=int(kwargs['gid'])),\
                                             community=Community.objects.get(id=int(cid)),\
                                             community_owner=User.objects.get(id=int(uid)))
            context = {}
            message = ''
            context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True, approved=False)
            context['uid'] = uid
            context['cid'] = cid
            return context    
   
    class ReportView(TemplateView):
        template_name='hs_community_mgmt/denied.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            context = {}
            message = ''
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))    
                if kwargs['action'] == 'remove_group':
                    user = User.objects.get(id=int(uid))
                    if user.uaccess.can_unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                            this_group=Group.objects.get(id=int(kwargs['gid']))):
                            user.uaccess.unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                            this_group=Group.objects.get(id=int(kwargs['gid'])))
            context['uid'] = uid
            context['cid'] = cid
            context['community'] = Community.objects.get(id=int(cid))
            return context 
   
    class Functions(TemplateView):
        template_name='hs_community_mgmt/comm_functions.html'

    class Invite_Group(TemplateView):
        template_name='hs_community_mgmt/invite_group.html'
        def get_context_data(request, uid, cid, *args, **kwargs):
            context = {}
            message = ''
            if 'action' in kwargs:
                logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
                if kwargs['action'] == 'invite_group':
                    message, worked = GroupCommunityRequest.create_or_update(group=Group.objects.get(id=int(kwargs['gid'])), \
                                                                         community=Community.objects.get(id=int(cid)), \
                                                                         requester=User.objects.get(id=int(uid)))
                    logger.debug("message = '{}' worked='{}'".format(message, worked))
                    context['message'] = message
                    context['worked'] = worked
            context['uid'] = uid
            context['cid'] = cid
            context['community'] = Community.objects.get(id=int(cid))
            return context
 
    def get_context_data(request, uid, cid, *args, **kwargs):
        context = {}
        message = ''
        if 'action' in kwargs:
            logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
            if kwargs['action'] == 'approve':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid), group__id=int(kwargs['gid']))
                message, worked  = gcr.approve(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'decline':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'cancel':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.cancel(requester=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'invite_group':
                message, worked = GroupCommunityRequest.create_or_update(group=Group.objects.get(id=int(kwargs['gid'])), \
                                                                         community=Community.objects.get(id=int(cid)), \
                                                                         requester=User.objects.get(id=int(uid)))
                debugger = logger.debug("message = '{}' worked='{}'".format(message, worked))
                context['message'] = debugger
                context['worked'] = worked
            elif kwargs['action'] == 'delete':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.remove(requester=User.objects.get(id=int(uid)),\
                                             group=Group.objects.get(id=int(kwargs['gid'])),\
                                             community=Community.objects.get(id=int(cid)),\
                                             community_owner=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['gcall'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)))
        context['redeemed'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True)
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True, approved=False)
        return context
   
class CommandView(TemplateView):
    template_name = 'hs_community_mgmt/comm.html'
    def get_context_data(request, uid, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

class LearnView(TemplateView):
    template_name = 'hs_community_mgmt/learn.html'
    def get_context_data(request, uid, cid, *args, **kwargs):
        message = ''
        context = {}
        if 'action' in kwargs:
            logger.debug("uid={}, cid={}, action={}"
                         .format(uid, cid, kwargs['action']))
            if kwargs['action'] == 'approve':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid), group__id=int(kwargs['gid']))
                message, worked  = gcr.approve(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'decline':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.decline(responder=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'cancel':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.cancel(requester=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'invite_group':
                message, worked = GroupCommunityRequest.create_or_update(group=Group.objects.get(id=int(kwargs['gid'])), \
                                                       community=Community.objects.get(id=int(cid)), \
                                                       requester=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'delete':
                gcr = GroupCommunityRequest.objects.get(community__id=int(cid),
                                                        group__id=int(kwargs['gid']))
                message, worked = gcr.remove(requester=User.objects.get(id=int(uid)),\
                                             group=Group.objects.get(id=int(kwargs['gid'])),\
                                             community=Community.objects.get(id=int(cid)),\
                                             community_owner=User.objects.get(id=int(uid)))
                logger.debug("message = '{}' worked='{}'".format(message, worked))
            elif kwargs['action'] == 'remove_group':
                user = User.objects.get(id=int(uid))
                if user.uaccess.can_unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                        this_group=Group.objects.get(id=int(kwargs['gid']))):
                        user.uaccess.unshare_community_with_group(this_community=Community.objects.get(id=int(cid)), \
                                                                        this_group=Group.objects.get(id=int(kwargs['gid'])))
            elif kwargs['action'] == 'change_user':
                logger.debug("message = '{}' worked='{}'".format("Work in progress", "<--"))
                context['uid'] = int(uid)
                context['cid'] = int(cid)
                user = User.objects.get(id=int(uid))
                context['community'] = Community.objects.get(id=int(cid))
                context['owned_communities'] = Community.objects.filter(id=int(cid), c2ucp__user=user, c2ucp__privilege=PrivilegeCodes.OWNER)
                context['uinfo'] = {'user': user, 'id' : user.uaccess.id, 'groups' : user.uaccess.my_groups}
                context['comm_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
                context['groups'] = Group.objects.all()
                context['users'] = User.objects.all()
                context['gcr'] = GroupCommunityRequest.objects.filter(community__id=int(cid),
                                         redeemed=False, community__c2ucp__user=user)
                context['gcall'] = GroupCommunityRequest.objects.filter(community__id=int(cid),
                                                                        community__c2ucp__user=user, community__c2ucp__privilege=PrivilegeCodes.OWNER)
                context['redeemed'] = GroupCommunityRequest.objects.filter(community__id=int(cid), redeemed=True, community__c2ucp__user=user,
                                                                           community__c2ucp__privilege=PrivilegeCodes.OWNER)
                context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True, approved=False)
                return context
            else:
                message = "improper action '{}'".format(kwargs['action'])
                logger.error(message)
        context['message'] = message
        context['uid'] = uid
        context['cid'] = cid
        context['community'] = Community.objects.get(id=int(cid))
        context['comm_owners'] = User.objects.filter(u2ucp__privilege=PrivilegeCodes.OWNER)
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['gcall'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)))
        context['redeemed'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=True)
        context['gcr'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), redeemed=False)
        context['denied'] = GroupCommunityRequest.objects.filter(community=Community.objects.get(id=int(cid)), approved=False)
        context['all_groups'] = Group.objects.all()
        return context
            


def get_user_info(request, uid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    dic = {'first' : user.first_name, 'last' : user.last_name, 'id' : user.uaccess.id}
    return JsonResponse(dic, safe=False)

def accept_community_request(request, gid, uid, cid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    c = int(cid)
    comm = Community.objects.get(id=c)
    g = int(gid)
    group = Group.objects.getW(id=g)
    gcr = GroupCommunityRequest.create_or_update(group=group, community=comm, requester=user)
    key = gcr.values_list('pk')
    gcr = GroupCommunityRequest.get(pk=key)  # put gcr.pk into the link.
    gcr.approve(u)
    return True
    

def get_community_info(request, cid, *args, **kwargs):
    c = int(cid)
    comm = Community.objects.get(id=c)
    owns = list()
    member_groups = list()
    member_users = list()
    public_resources = list()
    for r in comm.public_resources:
        public_resources.append(str(r))
    for u in comm.member_users:
        member_users.append(user_obj_to_string(u))
    for g in comm.member_groups:
        member_groups.append(get_member_group_info(g.id))
    for i in comm.owners:
        owns.append(user_obj_to_string(i))
    gcr = GroupCommunityRequest.objects.filter(community=comm, redeemed=False).values_list('community__name',\
                     'community__id', 'group_owner__username', 'group_owner__id',\
                             'group__name', 'group__id', 'when_requested', 'pk')
    redeemed = GroupCommunityRequest.objects.filter(redeemed=True).values_list('community__name',\
                     'community__id', 'community_owner', 'group_owner__username', 'group_owner__id',\
                             'group__name', 'group__id', 'when_responded', 'pk')
    dic = {'name' : comm.name, 'id' : comm.id, 'owners' : owns, 'member_groups'\
                 : member_groups, 'member_users' : member_users, \
                 'public_resources' : public_resources,  'requests': list(),\
                 'redeemed' : list()}
    for i in gcr:
        dic['requests'].append({'gname': str(i[4]), 'gid' : str(i[5]), 'gowner' : str(i[2]),\
                                'gownerid' : str(i[3]), 'dateofreq': str(i[6]), 'rid' : str(i[7])})
    for r in redeemed:
        dic['redeemed'].append({'gname': str(r[4]), 'gid' : str(r[6]), 'gowner' : str(r[3]), \
                                'gownerid' : str(r[4]), 'dateofred': str(r[7]), \
                                        'rid' : str(r[8]), 'cowner' : str(r[2])})
    return JsonResponse(dic, safe=False)

def get_member_group_info(gid):
    group = Group.objects.get(id=gid)
    gcr = GroupMembershipRequest.objects.filter(group_to_join=group).values_list('request_from',\
                                 'date_requested')
    mems = list()
    for u in group.gaccess.members:
        mems.append(user_obj_to_string(u))
    dic  = {'name': str(group), 'id' : gid, 'owner' : user_obj_to_string(group.gaccess.first_owner),\
                             'size' : len(mems),\
                             'members' : mems, 'requests': {}}
    for i in gcr:
        subdic = {'from': i[0], 'date' : i[1]}
        dic['requests'].update(subdic)
    return dic

def get_group_info(request, gid, *args, **kwargs):
        g = int(gid)
        group = Group.objects.get(id=g)
        gcr = GroupMembershipRequest.objects.filter(group_to_join=group).values_list('request_from',\
                                 'date_requested')
        mems = list()
        for u in group.gaccess.members:
            mems.append(user_obj_to_string(u))
        dic  = {'id' : g, 'owner' : user_obj_to_string(group.gaccess.first_owner),\
                                 'size' : len(mems),\
                                 'members' : mems, 'requests': {}}
        for i in gcr:
            subdic = {'from': i[0], 'date' : i[1]}
            dic['requests'].update(subdic)
        return JsonResponse(dic, safe=False)

def user_obj_to_string(user):
    name = str(user.first_name) + " " + str(user.last_name)
    return name

def load_utable_data(request, uid, *args, **kwargs):
    return "CUAHSI"

def gdata(request, gid, *args, **kwargs):
    g = int(gid)
    group = Group.objects.get(id=g)
    return JsonResponse({"name": group.name, "id": group.id})


def user_community_approve(request, uid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    gcr = GroupCommunityRequest.pending(user).filter(
        community__isnull=True,
        community__c2ucp__privilege=PrivilegeCodes.OWNER,
        community__c2ucp__user=user)\
        .values_list('community_owner', 'community', 'group_owner', 'group')
    return JsonResponse(gcr, safe=False)


def user_owned_groups(request, uid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    groups = Group.objects.filter(g2ugp__user=user,
                                  g2ugp__privilege=PrivilegeCodes.OWNER)\
        .values_list('name', 'id', 'gaccess__description', 'gaccess__purpose')
    return JsonResponse(list(groups), safe=False)


def user_owned_communities(request, uid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    communities = Community.objects.filter(c2ucp__user=user,
                                             c2ucp__privilege=PrivilegeCodes.OWNER)\
        .values_list('name', 'id', 'description', 'purpose')
    return JsonResponse(list(communities), safe=False)


def user_community_pending(request, uid, cid, *args, **kwargs):
    u = int(uid)
    user = User.objects.get(id=u)
    c = int(cid)
    community = Community.objects.get(id=c)
    if user.uaccess.owns_community(community):
        gcr = GroupCommunityRequest.pending(user).filter(community=community,
                                                         community_owner__isnull=True)\
            .values_list('community__name', 'community__id', 'group_owner__username',
                         'group_owner__id', 'group__name', 'group__id')
        return JsonResponse(gcr, safe=False)
    else:
        return JsonResponse([], safe=False)
