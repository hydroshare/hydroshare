"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


def measure_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    istorage = resource.get_irods_storage()
    if istorage.exists(resource.file_path): 
        print("{} {}".format(resource.size, short_id))
    else: 
        print("{} {} no file path".format(0, short_id))


class Command(BaseCommand):
    help = "Print size information."

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
                measure_resource(rid)

        else:
            for r in BaseResource.objects.all():
                storage = r.get_irods_storage()
                if storage.exists(r.root_path):
                    measure_resource(r.short_id)
                else: 
                    print("{} does not exist in iRODS".format(r.short_id))
