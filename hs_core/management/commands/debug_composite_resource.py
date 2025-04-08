"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from pprint import pprint


def debug_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    if resource.resource_type == 'CompositeResource':
        # first dump the data from each logical file
        for f in resource.files.all():
            if f.has_logical_file:
                metadata = f.metadata.get_html()
                print("metadata for {} is".format(resource.short_id))
                pprint(metadata)

        resource.create_aggregation_meta_files()
        print("resource {}".format(resource.short_id))
        '''
        storage = resource.get_s3_storage()
        single_file_aggregation has been removed
        for f in ResourceFile.objects.filter(object_id=resource.id):
            if f.has_logical_file and f.logical_file.is_single_file_aggregation:
                print("  {} is single file aggregation {} "
                      .format(f.short_path,
                              f.logical_file.get_aggregation_type_name()))
                if not storage.exists(f.storage_path):
                    print("    {} does not exist".format(f.storage_path))
                if not storage.exists(f.storage_path + "_resmap.xml"):
                    print("    {} does not exist".format(f.storage_path + "_resmap.xml"))
                if not storage.exists(f.storage_path + "_meta.xml"):
                    print("    {} does not exist".format(f.storage_path + "_meta.xml"))
         '''


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
