# -*- coding: utf-8 -*-

"""
Check Django metadata

This checks that:

1. Every resource has a metadata entry.
2. Every metadata entry has a title.

More tests are left for later.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource

import logging


def check_django_metadata(self, stop_on_error=False,
                          echo_errors=True,
                          log_errors=False,
                          return_errors=False):

    # print("check_django_metadata: check {}".format(self.short_id))
    logger = logging.getLogger(__name__)
    istorage = self.get_s3_storage()
    errors = []
    ecount = 0

    # flag non-existent resources in storage
    if not istorage.exists(self.root_path):
        msg = "root path {} does not exist in storage".format(self.root_path)
        ecount += 1
        if echo_errors:
            print(msg)
        if log_errors:
            logger.error(msg)
        if return_errors:
            errors.append(msg)

    # basic check: metadata exists
    if self.metadata is None:
        msg = "metadata for {} does not exist".format(self.short_id)
        ecount += 1
        if echo_errors:
            print(msg)
        if log_errors:
            logger.error(msg)
        if return_errors:
            errors.append(msg)

    elif self.metadata.title is None:
        msg = "{} has no title".format(self.short_id)
        ecount += 1
        if echo_errors:
            print(msg)
        if log_errors:
            logger.error(msg)
        if return_errors:
            errors.append(msg)

    return errors, ecount


class Command(BaseCommand):
    help = "Check existence of proper Django metadata."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',  # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)
                    continue

                print("LOOKING FOR METADATA ERRORS FOR RESOURCE {}".format(rid))
                check_django_metadata(resource, stop_on_error=False,
                                      echo_errors=not options['log'],
                                      log_errors=options['log'],
                                      return_errors=False)

        else:  # check all resources
            print("LOOKING FOR METADATA ERRORS FOR ALL RESOURCES")
            for r in BaseResource.objects.all():
                check_django_metadata(r, stop_on_error=False,
                                      echo_errors=not options['log'],  # Don't both log and echo
                                      log_errors=options['log'],
                                      return_errors=False)
