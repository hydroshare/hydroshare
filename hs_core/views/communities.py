from __future__ import absolute_import

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

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

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(FindCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # user_id = User.objects.get(pk=self.request.user.id)
        grpfilter = self.request.GET.get('grp')

        # community_resources = community_from_name_or_id("CZO National Community").public_resources

        # for c in Community.objects.all():
        #     print("  '{}' (id={})".format(c.name, str(c.id)))

        # for c in community_resources:
        #     if not any(str(c.group_id) == g.get('id') for g in groups):  # if the group id is not already present in the list
        #         if c.group_name != "CZO National":  # The National Group is used to establish the entire Community
        #             groups.append({'id': str(c.group_id), 'name': str(c.group_name)})

        return {
            'communities_list': Community.objects.all()
        }


class MyCommunitiesView(TemplateView):
    template_name = 'pages/my-communities.html'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(MyCommunitiesView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        # user_id = User.objects.get(pk=self.request.user.id)
        grpfilter = self.request.GET.get('grp')

        # community_resources = community_from_name_or_id("CZO National Community").public_resources

        # for c in Community.objects.all():
        #     print("  '{}' (id={})".format(c.name, str(c.id)))

        # for c in community_resources:
        #     if not any(str(c.group_id) == g.get('id') for g in groups):  # if the group id is not already present in the list
        #         if c.group_name != "CZO National":  # The National Group is used to establish the entire Community
        #             groups.append({'id': str(c.group_id), 'name': str(c.group_name)})

        return {
            'communities_list': Community.objects.all()
        }