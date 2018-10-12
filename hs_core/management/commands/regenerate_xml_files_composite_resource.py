"""Generate bag files composite resources. Regeneration of bag files is needed to get the
resource level xml files corrected as well as to generate aggregation level
xml files which currently does not exist for any of the composite resources created prior to
composite resource phase-2 implementation

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand

from hs_core.hydroshare import create_bag_files
from hs_composite_resource.models import CompositeResource


class Command(BaseCommand):
    help = "Generate bag files for specified composite resources"

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):
        resource_counter_success = 0
        resource_counter = 0

        # inner function
        def generate_bag_files(resource):
            metadata_status = {}
            for aggregation in resource.logical_files:
                is_dirty = aggregation.metadata.is_dirty
                metadata_status[aggregation.id] = is_dirty
                # this is needed to generate aggregation level xml files
                aggregation.metadata.is_dirty = True
                aggregation.metadata.save()
            print("> GENERATING BAG FILES FOR COMPOSITE RESOURCE:{}".format(resource.short_id))
            create_bag_files(resource)
            print(">> GENERATED BAG FILES FOR COMPOSITE RESOURCE:{}".format(resource.short_id))
            # re-set metadata status
            for aggregation in resource.logical_files:
                aggregation.metadata.is_dirty = metadata_status[aggregation.id]
                aggregation.metadata.save()

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = CompositeResource.objects.get(short_id=rid)
                    resource_counter += 1
                    generate_bag_files(resource)
                    resource_counter_success += 1
                except CompositeResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)
                    continue

        else:  # check all composite resources and create bag files
            print("> GENERATING BAG FILES FOR ALL COMPOSITE RESOURCES")
            for r in CompositeResource.objects.all():
                resource_counter += 1
                generate_bag_files(r)
                resource_counter_success += 1

        print(">> {} COMPOSITE RESOURCES PROCESSED.".format(resource_counter))
        print(">> BAG FILES GENERATED FOR {} COMPOSITE RESOURCES.".format(resource_counter_success))
