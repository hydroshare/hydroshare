# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView  # ListView
from hs_explore.models import RecommendedResource, RecommendedUser, \
    RecommendedGroup, Status
from hs_core.models import get_user


class RecommendList(TemplateView):
    """ Get the top five recommendations for resources, users, groups """
    template_name = 'recommendations.html'
    
    def get_context_data(self, **kwargs):

        context = super(RecommendList, self).get_context_data(**kwargs)
        
        user = get_user(self.request)
        username = user.username
        context['resource_list'] = RecommendedResource.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        # mark relevant records as shown
        for r in context['resource_list']:
            if r.state == Status.STATUS_NEW:
                r.shown()

        context['user_list'] = RecommendedUser.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        # mark relevant records as shown
        for r in context['user_list']:
            if r.state == Status.STATUS_NEW:
                r.shown()

        context['group_list'] = RecommendedGroup.objects\
            .filter(state__lte=Status.STATUS_EXPLORED, user__username=username)\
            .order_by('-relevance')[:Status.RECOMMENDATION_LIMIT]

        # mark relevant records as shown
        for r in context['group_list']:
            if r.state == Status.STATUS_NEW:
                r.shown()
        return context
