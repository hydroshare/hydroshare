import datetime
import json
import logging
import time
from collections import namedtuple

from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from haystack.inputs import Exact
from rest_framework.views import APIView

logger = logging.getLogger(__name__)


class PublicationView(TemplateView):

    def get(self, request, *args, **kwargs):
        return render(request, 'hs_publication/index.html', {'sample_data': 'hello world'})


class PublicationAPI(APIView):

    def __init__(self, **kwargs):
        super(PublicationAPI, self).__init__(**kwargs)
        self.value = None

    def get(self, request, *args, **kwargs):
        print(f"hello world")
