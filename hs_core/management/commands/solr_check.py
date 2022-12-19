"""Checks the data ingested into SOLR for unqualified search terms
"""

from django.core.management.base import BaseCommand
from haystack.query import SearchQuerySet
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Debug solr contents."

    def add_arguments(self, parser):

        # a list of resource id's: none acts on everything.
        parser.add_argument("resource_ids", nargs="*", type=str)

    def handle(self, *args, **options):

        if len(options["resource_ids"]) > 0:  # an array of resource short_id to check.
            for rid in options["resource_ids"]:
                sqs = SearchQuerySet().filter(short_id=rid)
                for s in list(sqs):
                    print("SOLR FOR RESOURCE {}: {}".format(rid, s.text))
                    print("SOLR variables: {}".format(s.variable))

        else:
            for resource in BaseResource.objects.filter(raccess__discoverable=True):
                sqs = SearchQuerySet().filter(short_id=resource.short_id)
                for s in list(sqs):
                    print("SOLR FOR RESOURCE {}: {}".format(resource.short_id, s.text))
                    print("SOLR variables: {}".format(s.variable))
