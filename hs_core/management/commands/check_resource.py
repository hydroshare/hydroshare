"""This does a comprehensive test of a resource.

This checks:
* S3 files
* AVU values
* Existence of Logical files

Notes:
* By default, this script prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import CheckResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Print results of testing resource integrity."

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

        parser.add_argument(
            '--type',
            dest='type',
            help='limit to resources of a particular type'
        )

        parser.add_argument(
            '--storage',
            dest='storage',
            help='limit to specific storage medium (local, user, federated)'
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                if (options['type'] is None or resource.resource_type == options['type']) and \
                   (options['storage'] is None or resource.storage_type == options['storage']):
                    CheckResource(rid).test()
        else:
            for resource in BaseResource.objects.all():
                if (options['type'] is None or resource.resource_type == options['type']) and \
                   (options['storage'] is None or resource.storage_type == options['storage']):
                    CheckResource(resource.short_id).test()
