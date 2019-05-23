"""
Set resource(s) relevant AVUs to dirty so that resource xml files and resource bag
gets regenerated prior to download

"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


def set_resource_dirty(rid):
    try:
        resource = BaseResource.objects.get(short_id=rid)
        resource.setAVU('metadata_dirty', 'true')
        resource.setAVU('bag_modified', 'true')
        print("Resource with id {} was set dirty.".format(rid))
    except BaseResource.DoesNotExist:
        print(">> Resource with id {} NOT FOUND in Django".format(rid))


class Command(BaseCommand):
    help = "Set resource 'metadata_dirty' and 'bag_modified' AVUs to true"

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                set_resource_dirty(rid)
        else:
            print("> SETTING ALL RESOURCES DIRTY")
            for res in BaseResource.objects.all():
                set_resource_dirty(res.short_id)