"""
Instantiate resource ID's for tracking records.
"""
from django.core.management.base import BaseCommand
import re
from hs_tracking.models import Variable


def instantiate_resource_ids():
    re_compiler = {"visit": re.compile('/resource/([^/]+)/'),
                   "download": re.compile('\|resource_guid=([^|]+)\|'),
                   "app_launch": re.compile('\|resourceid=([^|]+)\|')}
    for v in Variable.objects.all():
        value = v.get_value()
        m = re_compiler[v.name].search(value)
        if (m and m.group(1)):
            resource_id = m.group(1)
            if(resource_id is not None):
                v.resource_id = resource_id
                v.save()


class Command(BaseCommand):
    help = "Instantiate all resource id's for tracking."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        instantiate_resource_ids()
