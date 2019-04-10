"""
This prints the state of a facet query.
It is used for debugging the faceting system.
"""

from django.core.management.base import BaseCommand
from haystack.query import SearchQuerySet
from hs_core.discovery_parser import ParseSQ


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('queries', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['queries']) > 0:  # an array of resource short_id to check.
            query = ' '.join(options['queries'])
            sqs = SearchQuerySet().all()
            parser = ParseSQ()
            parsed = parser.parse(query)
            sqs = sqs.filter(parsed)
            print("QUERY '{}' PARSED {}".format(query, str(parsed)))
            for result in list(sqs):
                stored = result.get_stored_fields()
                print("  {}: {} {} {} {}".format(
                    unicode(stored['short_id']).encode('ascii', 'replace'),
                    unicode(stored['title']).encode('ascii', 'replace'),
                    unicode(stored['author']).encode('ascii', 'replace'),
                    unicode(stored['created']).encode('ascii', 'replace'),
                    unicode(stored['modified']).encode('ascii', 'replace')))

        else:
            print("no queries to try")
