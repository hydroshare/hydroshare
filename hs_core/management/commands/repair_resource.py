# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile
3. every iRODS directory {short_id} corresponds to a Django resource

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.management.utils import repair_resource

import logging


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):

        # id of the resource to repair
        parser.add_argument('resource_id', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',  # value is options['log']
            help='log errors to system log',
        )
        parser.add_argument(
            '--dryrun',
            action='store_true',  # True for presence, False for absence
            dest='dry_run',  # value is options['dry_run']
            help='run process without saving changes',
        )

    def handle(self, *args, **options):

        logger = logging.getLogger(__name__)
        log_errors = options['log']
        echo_errors = not options['log']
        rid = options['resource_id']
        dry_run = options['dry_run']

        try:
            resource = get_resource_by_shortkey(rid, or_404=False)
        except BaseResource.DoesNotExist:
            msg = "resource {} not found".format(rid)
            if log_errors:
                logger.error(msg)
            if echo_errors:
                print(msg)
            return

        repair_resource(resource, logger, dry_run=dry_run)
