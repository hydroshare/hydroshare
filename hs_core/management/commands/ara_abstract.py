from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.features import Features
from django.contrib.auth.models import Group
from hs_explore.utils import Utils
from hs_explore.topic_modeling import TopicModeling
from datetime import datetime
from pprint import pprint
import pickle
import sys


class Command(BaseCommand):
    help = "Print abstract for a resource."

    def handle(self, *args, **options):
        for res in BaseResource.objects.all():
            x = Features.resource_extended_abstract(res)
            pprint(x)
            print("")
