"""
This prints the state of a facet query.
It is used for debugging the faceting system.
"""

from django.core.management.base import BaseCommand
from haystack.query import SearchQuerySet
import json
from pprint import pprint


def debug_query_json(rid):
    sqs = SearchQuerySet().all().filter(short_id=rid)
    for result in list(sqs):
        print("FETCHING STORED JSON")
        stored = result.get_stored_fields()
        js = stored['json']
        print(js)
        print("INTERPRETING STORED JSON")
        foo = json.loads(js)
        pprint(foo)


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        for rid in options['resource_ids']:
            debug_query_json(rid)
