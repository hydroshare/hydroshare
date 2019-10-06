"""List the content types of resources for debugging.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
import mimetypes
from hs_core.search_indexes import BaseResourceIndex
from haystack.query import SearchQuerySet


def get_ext(name):
    stuff = name.split('.')
    if len(stuff) == 1:
        return None
    candidate = stuff[len(stuff)-1]
    if '/' in candidate or candidate.startswith('_'):
        return None
    return candidate


def get_mime(ext):
    if ext is not None:
        guess = mimetypes.guess_type("foo."+ext)
        return guess[0]
    else:
        return "none"


class Command(BaseCommand):
    help = "Print logical file information."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        ind = BaseResourceIndex()
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    r = BaseResource.objects.get(short_id=rid)
                    if ind.should_update(r):
                        print("resource {} needs updating".format(rid))
                        ind.update_object(r)
                except BaseResource.DoesNotExist:
                    print("resource {} does not exist in Django".format(rid))

        else:

            sqs = SearchQuerySet().all()
            print("SOLR count = {}".format(sqs.count()))
            dqs = BaseResource.objects.filter(Q(raccess__discoverable=True) |
                                              Q(raccess__public=True))
            print("Django count = {}".format(dqs.count()))

            # what is in Django that isn't in SOLR:
            found = set()
            count = 0
            for r in list(sqs):
                found.add(r.short_id)
                # resource = get_resource_by_shortkey(r.short_id)
                # print("{} {} found".format(r.short_id, resource.discovery_content_type))
            for r in dqs:
                resource = get_resource_by_shortkey(r.short_id)
                if r.short_id not in found:
                    print("{} {} NOT FOUND in SOLR: adding to index".format(
                            r.short_id, resource.discovery_content_type))
                    count += 1
                    ind.update_object(r)
                # # This always returns True whether or not SOLR needs updating
                # elif ind.should_update(r):
                #     print("{} {} needs SOLR update: updating in index".format(
                #             r.short_id, resource.discovery_content_type))
                #     ind.update_object(r)
                #     count += 1

            print("{} resources in Django refreshed in SOLR".format(count))

            # what is in SOLR that isn't in Django:
            found = set()
            count = 0
            for r in list(dqs):
                found.add(r.short_id)
                # resource = get_resource_by_shortkey(r.short_id)
                # print("{} {} found".format(r.short_id, resource.discovery_content_type))
            for r in sqs:
                if r.short_id not in found:
                    resource = get_resource_by_shortkey(r.short_id)
                    print("{} {} NOT FOUND in Django; removing from SOLR".format(
                            r.short_id, resource.discovery_content_type))
                    ind.remove_object(r)
                    count += 1
            print("{} resources in not in Django removed from SOLR".format(count))
