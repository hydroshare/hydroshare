# -*- coding: utf-8 -*-

"""
This calls all preparation routines involved in creating SOLR records.
It is used to debug SOLR harvesting. If any of these routines fails on
any resource, all harvesting ceases. This has caused many bugs.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.models import BaseResource
from hs_core.search_indexes import BaseResourceIndex
from pprint import pprint
import json


def debug_harvest(rid):
    ind = BaseResourceIndex()
    obj = BaseResource.objects.get(short_id=rid)
    print(("TESTING RESOURCE {}".format(obj.title)))
    js = ind.prepare(obj)
    print(js['json']) 
    print("LoADING JSON")
    foo = json.loads(js['json'])
    print("PRINTING STRUCTURE")
    pprint(foo)

class Command(BaseCommand):
    help = "Print debugging information about json templating."

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        for rid in options['resource_ids']: 
            debug_harvest(rid)

