from django.conf import settings
from django.shortcuts import render
from django.views.generic import TemplateView


class SearchView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'discovery_atlas/index.html')
