# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView  # ListView
from hs_explore.models import RecommendedResource, RecommendedUser, \
    RecommendedGroup, Status


class RecommendList(TemplateView):
    template_name = 'recommendations.html'

    def get_context_data(self, **kwargs):
        context = super(RecommendList, self).get_context_data(**kwargs)
        context['resource_list'] = RecommendedResource.objects\
            .filter(status__le=Status.STATUS_EXPLORED)\
            .order_by('-relevance')\
            .limit(Status.RECOMMENDATION_LIMIT)
        context['user_list'] = RecommendedUser.objects\
            .filter(status__le=Status.STATUS_EXPLORED)\
            .order_by('-relevance')\
            .limit(Status.RECOMMENDATION_LIMIT)
        context['group_list'] = RecommendedGroup.objects\
            .filter(status__le=Status.STATUS_EXPLORED)\
            .order_by('-relevance')\
            .limit(Status.RECOMMENDATION_LIMIT)
        return context
