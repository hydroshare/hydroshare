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
from hs_core.management.utils import repair_resource, check_time

import logging
import time


def log_or_echo(message, log_errors, logger):
    if log_errors:
        logger.info(message)
    else:
        print(message)


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

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
        parser.add_argument(
            '--timeout',
            action='store_true',
            dest='timeout',
            help='limit runtime to X seconds',
        )

    def handle(self, *args, **options):

        logger = logging.getLogger(__name__)
        log_errors = options['log']
        echo_errors = not options['log']
        time_out = options['timeout']
        start_time = time.time()

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    if time_out:
                        check_time(start_time, time_out)
                    resource = get_resource_by_shortkey(rid)
                    repair_resource(resource, logger,
                                    echo_errors=echo_errors,
                                    log_errors=log_errors,
                                    return_errors=False)
                except BaseResource.DoesNotExist:
                    msg = "resource {} not found".format(rid)
                    log_or_echo(msg, log_errors, logger)
                    continue
                except TimeoutError:
                    log_or_echo(f"Terminating repair_resource job -- \
                                {time_out} second time limit has elapsed", log_errors, logger)
                    break

        else:  # check all resources
            log_or_echo("REPAIRING ALL RESOURCES", log_errors, logger)
            for r in BaseResource.objects.all():
                try:
                    if time_out:
                        check_time(start_time, time_out)
                    resource = get_resource_by_shortkey(r.short_id)
                    repair_resource(resource, logger,
                                    echo_errors=echo_errors,
                                    log_errors=log_errors,
                                    return_errors=False)
                except BaseResource.DoesNotExist:
                    msg = "resource {} not found".format(r.short_id)
                    log_or_echo(msg, log_errors, logger)
                    continue
                except TimeoutError:
                    log_or_echo(f"Terminating repair_resource job -- \
                                {time_out} second time limit has elapsed", log_errors, logger)
                    break
