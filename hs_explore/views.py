# from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView  # ListView
from hs_explore.models import RecommendedResource, RecommendedUser, RecommendedGroup


class RecommendList(TemplateView):
    template_name='recommendations.html'
    def get_context_data(self, **kwargs):
        context = super(RecommendList, self).get_context_data(**kwargs)
        context['resource_list'] = RecommendedResource.objects.all()
        context['user_list'] = RecommendedUser.objects.all()
        context['group_list'] = RecommendedGroup.objects.all()
        return context
