from __future__ import absolute_import

import json
import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.utils.html import mark_safe, escapejs
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache
from hs_access_control.management.utilities import community_from_name_or_id
from hs_access_control.models.community import Community
from hs_communities.models import Topic

logger = logging.getLogger(__name__)


class CollaborateView(TemplateView):
    template_name = 'pages/collaborate.html'


class CommunitiesView(TemplateView):
    template_name = 'pages/communities.html'

    def dispatch(self, *args, **kwargs):
        return super(CommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # user_id = User.objects.get(pk=self.request.user.id)
        grpfilter = self.request.GET.get('grp')

        community_resources = community_from_name_or_id("CZO National Community").public_resources
        groups = []
        for c in community_resources:
            if not any(str(c.group_id) == g.get('id') for g in groups):  # if the group id is not already present in the list
                if c.group_name != "CZO National":  # The National Group is used to establish the entire Community
                    groups.append({'id': str(c.group_id), 'name': str(c.group_name)})

        groups = sorted(groups, key=lambda key: key['name'])
        return {
            'community_resources': community_resources,
            'groups': groups,
            'grpfilter': grpfilter
        }


class FindCommunitiesView(TemplateView):
    template_name = 'pages/find-communities.html'

    def dispatch(self, *args, **kwargs):
        return super(FindCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):

        return {
            'communities_list': Community.objects.all()
        }


@method_decorator(login_required, name='dispatch')
class MyCommunitiesView(TemplateView):
    template_name = 'pages/my-communities.html'

    def dispatch(self, *args, **kwargs):
        return super(MyCommunitiesView, self).dispatch(*args, **kwargs)

    def group_to_community(self, grp, C):
        """
        return the community membership information of a group; group can belong to only one community
        :param grp: Group object
        :param C: Community class object
        :return: tuple id, name of community
        """
        for community in C.objects.all():
            if grp.id in [g.id for g in community.member_groups]:
                return (community.id, community.name)

    def get_context_data(self, **kwargs):
        all_communities = Community.objects.all()

        u = User.objects.get(pk=self.request.user.id)
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = u in g.gaccess.members
            g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
            g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
            g.join_request = None
            if g.join_request_waiting_owner_action or g.join_request_waiting_user_action:
                g.join_request = g.gaccess.group_membership_requests.filter(request_from=u).first() or \
                                 g.gaccess.group_membership_requests.filter(invitation_to=u).first()

        comm_groups = Community.objects.all()[0]
        member_of = dict()
        for comm in Community.objects.all():
            if u.id in [m.id for m in comm.member_users] or u.id in [o.id for o in comm.owners]:
                member_of[comm.id] = comm.name

        return {
            'communities_list': all_communities
        }


@method_decorator(login_required, name='dispatch')
class TopicsView(TemplateView):
    """
    TODO log failure and silently redirect to view if missing params

    id:
    name:
    action: CREATE, READ, UPDATE, DELETE
    """

    def get(self, request, *args, **kwargs):
        return render(request, 'pages/topics.html', {'topics_json': self.get_context_data()})

    def post(self, request, *args, **kwargs):
        if request.POST.get('action') == 'CREATE':
            try:
                new_topic = Topic()
                new_topic.name = request.POST.get('name')
                new_topic.save()
            except Exception as e:
                logger.error("TopicsView error creating new topic {}".format(e))
        elif request.POST.get('action') == 'UPDATE':
            try:
                update_topic = Topic.objects.get(id=request.POST.get('id'))
                update_topic.name = request.POST.get('name')
                update_topic.save()
            except Exception as e:
                logger.error("TopicsView error updating topic {}".format(e))
        elif request.POST.get('action') == 'DELETE':
            try:
                delete_topic = Topic.objects.get(id=request.POST.get('id'))
                delete_topic.delete(keep_parents=False)
            except:
                logger.error("error")
        else:
            logger.error("TopicsView POST action not recognized should be CREATE UPDATE or DELETE")

        return HttpResponseRedirect('/topics/')

    def get_context_data(self, **kwargs):
        u = User.objects.get(pk=self.request.user.id)
        groups = Group.objects.filter(gaccess__active=True).exclude(name="Hydroshare Author")
        # for each group set group dynamic attributes
        for g in groups:
            g.is_user_member = u in g.gaccess.members
            g.join_request_waiting_owner_action = g.gaccess.group_membership_requests.filter(request_from=u).exists()
            g.join_request_waiting_user_action = g.gaccess.group_membership_requests.filter(invitation_to=u).exists()
            g.join_request = None
            if g.join_request_waiting_owner_action or g.join_request_waiting_user_action:
                g.join_request = g.gaccess.group_membership_requests.filter(request_from=u).first() or \
                                 g.gaccess.group_membership_requests.filter(invitation_to=u).first()

        topics = Topic.objects.all().values_list('id', 'name', flat=False).order_by('name')
        topics = list(topics)  # force QuerySet evaluation

        return mark_safe(escapejs(json.dumps(topics)))


# @api_view(['POST', 'GET'])
# def update_key_value_metadata_public(request, pk):
#     res, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
#
#     if request.method == 'GET':
#         return HttpResponse(status=200, content=json.dumps(res.extra_metadata))
#
#     post_data = request.data.copy()
#     res.extra_metadata = post_data
#
#     is_update_success = True
#
#     try:
#         res.save()
#     except Error as ex:
#         is_update_success = False
#
#     if is_update_success:
#         resource_modified(res, request.user, overwrite_bag=False)
#
#     if is_update_success:
#         return HttpResponse(status=200)
#     else:
#         return HttpResponse(status=400)