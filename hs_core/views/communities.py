from __future__ import absolute_import

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.contrib.auth.models import Group, User
from hs_access_control.management.utilities import community_from_name_or_id
from hs_access_control.models.community import Community




class CollaborateView(TemplateView):
    template_name = 'pages/collaborate.html'


class CommunitiesView(TemplateView):
    template_name = 'pages/communities.html'

    # @method_decorator(login_required)
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


        # all_communities[0].member_users[0].id
        # all_communities[0].owners