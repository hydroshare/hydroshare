# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

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
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found".format(rid)
                    print(msg)

                print("LOOKING FOR ERRORS FOR RESOURCE {}".format(rid))
                resource.check_irods_files(stop_on_error=False,
                                           echo_errors=not options['log'],
                                           log_errors=options['log'],
                                           return_errors=False)

        else:  # check all resources
            print("LOOKING FOR ERRORS FOR ALL RESOURCES")
            for r in BaseResource.objects.all():
                r.check_irods_files(stop_on_error=False,
                                    echo_errors=not options['log'],  # Don't both log and echo
                                    log_errors=options['log'],
                                    return_errors=False)
