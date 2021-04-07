"""
This tests sorting of SOLR resources.
"""

from django.core.management.base import BaseCommand
from haystack.query import SearchQuerySet


def debug_harvest():
    sqs = SearchQuerySet().all().order_by('author_lower')
    for s in sqs:
        print("author: " + s.author)
        print("author_lower: " + s.author_lower)


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        debug_harvest()
