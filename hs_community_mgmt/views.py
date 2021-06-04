from django.shortcuts import render

# Create your views here.

from django.views.generic import TemplateView


class TestView(TemplateView):
    template_name = 'hs_community_mgmt/test.html'
    def get_context_data(self, **kwargs):
        return {}
