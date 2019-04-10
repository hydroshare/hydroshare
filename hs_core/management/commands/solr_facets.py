"""
This prints the state of a facet query.
It is used for debugging the faceting system.
"""

from django.core.management.base import BaseCommand
from hs_core.discovery_form import FIELDS_TO_SHOW
from haystack.query import SearchQuerySet
from pprint import pprint


def debug_facets(facets):
    qs = SearchQuerySet().all()
    for field in facets:
        qs = qs.facet(field, sort='index', limit=-1)
    output = qs.facet_counts()
    pprint(output)


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('facet_fields', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['facet_fields']) > 0:  # an array of resource short_id to check.
            debug_facets(options['facet_fields'])

        else:
            debug_facets(FIELDS_TO_SHOW)
