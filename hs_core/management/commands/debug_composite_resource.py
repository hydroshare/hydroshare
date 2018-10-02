"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource, ResourceFile


def debug_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    if resource.resource_type == 'CompositeResource':
        storage = resource.get_irods_storage()
        resource.create_aggregation_xml_documents()
        print("resource {}".format(resource.short_id))
        expected_files = {}
        for l in resource.logical_files:
            expected_files[l.metadata_file_path] = 1
            expected_files[l.map_file_path] = 1
        for f in ResourceFile.objects.filter(object_id=resource.id):
            expected_files[f.storage_path] = 1
        for e in expected_files.keys():
            if not storage.exists(e):
                print("    {} does not exist".format(e))


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                debug_resource(rid)
        else:
            for r in BaseResource.objects.filter(resource_type="CompositeResource"):
                debug_resource(r.short_id)

            print("No resources to check.")
