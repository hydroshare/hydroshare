import datetime
import json
import logging
import time
from collections import namedtuple

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

DateRange = namedtuple('DateRange', ['start', 'end'])


class ResourceLandingView(TemplateView):

    def get(self, request, *args, **kwargs):
        maps_key = settings.MAPS_KEY if hasattr(settings, 'MAPS_KEY') else ''
        return render(request, 'hs_resource_landing/index.html', {'maps_key': maps_key})


class ResourceLandingAPI(APIView):

    def __init__(self, **kwargs):
        super(ResourceLandingAPI, self).__init__(**kwargs)

    def get(self, request, *args, **kwargs):
        """
        Description
        """
        start = time.time()

        return JsonResponse({
            'data': 'Sample Test Data',
            'time': (time.time() - start) / 1000
        }, status=200)
