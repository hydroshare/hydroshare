"""This does a comprehensive test of a resource.

This checks:
* IRODS files
* IRODS AVU values
* Existence of Logical files

Notes:
* By default, this script prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import TestResource


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

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                TestResource(rid).test()
        else:
            for r in BaseResource.objects.all():
                TestResource(r.short_id).test()
