""" This creates counts of what is in SOLR versus what is in Django for comparison.
    Note that in Django, publisher --> public --> discoverable, while in SOLR these
    are distinct facets.  """
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from haystack.query import SearchQuerySet


class Command(BaseCommand):
    help = "Compare SOLR records."

    def add_arguments(self, parser):

        # a list of resource id's: none acts on everything.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        count_disc_include = 0
        count_disc_exclude = 0
        count_disc_solr = 0
        discoverable = BaseResource.objects.filter(raccess__discoverable=True,
                                                   raccess__public=False)
        for d in discoverable:
            if d.show_in_discover:
                count_disc_include += 1
            else:
                count_disc_exclude += 1

        disc_solr = SearchQuerySet().filter(availability='discoverable').exclude(availability='public')
        count_disc_solr = disc_solr.count()

        print("discoverable shown={}, hidden={} solr={}"
              .format(count_disc_include, count_disc_exclude, count_disc_solr))

        count_public_include = 0
        count_public_exclude = 0
        count_public_solr = 0
        public = BaseResource.objects.filter(raccess__public=True,
                                             raccess__published=False)
        for d in public:
            if d.show_in_discover:
                count_public_include += 1
            else:
                count_public_exclude += 1

        disc_solr = SearchQuerySet().filter(availability='public').exclude(availability='published')
        count_public_solr = disc_solr.count()

        print("public shown={}, hidden={} solr={}"
              .format(count_public_include, count_public_exclude, count_public_solr))

        count_published_include = 0
        count_published_exclude = 0
        count_published_solr = 0
        published = BaseResource.objects.filter(raccess__published=True)
        for d in published:
            if d.show_in_discover:
                count_published_include += 1
            else:
                count_published_exclude += 1

        disc_solr = SearchQuerySet().filter(availability='published')
        count_published_solr = disc_solr.count()

        print("published shown={}, hidden={} solr={}"
              .format(count_published_include, count_published_exclude, count_published_solr))
