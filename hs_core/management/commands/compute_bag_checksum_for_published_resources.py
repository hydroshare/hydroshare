
from django.core.management.base import BaseCommand

from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.tasks import create_bag_by_s3


class Command(BaseCommand):
    help = "Generate bag checksums for published resources as needed"

    def add_arguments(self, parser):

        # a list of resource id's: if none, process all published resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                if resource.raccess.published:
                    create_bag_by_s3(rid)
                else:
                    print("Resource {} is not published, hence ignored.".format(rid))
        else:
            for resource in BaseResource.objects.filter(raccess__published=True):
                create_bag_by_s3(resource.short_id)
