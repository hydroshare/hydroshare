# -*- coding: utf-8 -*-

"""
Check synchronization between S3 and Django

This checks that every file in S3 corresponds to a ResourceFile in Django.
If a file in S3 is not present in Django, it attempts to register that file in Django.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource

from hs_core.management.utils import ingest_s3_files


import logging


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

        logger = logging.getLogger(__name__)
        log_errors = options['log']
        echo_errors = not options['log']

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    r = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    if log_errors:
                        logger.info(msg)
                    if echo_errors:
                        print(msg)
                    continue  # next resource

                # Pabitra: Not sure why are we skipping other resource types
                # Alva: cannot preserve file integrity constraints for other file types.
                if r.resource_type != 'CompositeResource':
                    print(("resource {} has type {}: skipping".format(r.short_id,
                                                                      r.resource_type)))
                else:
                    print("LOOKING FOR UNREGISTERED FILES FOR RESOURCE {} (current files {})"
                          .format(rid, str(r.files.all().count())))
                    # get the typed resource
                    try:
                        resource = r.get_content_model()
                    except Exception as e:
                        msg = "resource {} has no proxy resource: {}"\
                              .format(r.short_id, e.value)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)
                        msg = "... affected resource {} has type {}, title '{}'"\
                              .format(r.short_id, r.resource_type, r.title)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)
                        continue

                    _, count = ingest_s3_files(resource,
                                                  logger,
                                                  stop_on_error=False,
                                                  echo_errors=not options['log'],
                                                  log_errors=options['log'],
                                                  return_errors=False)
                    if count:
                        msg = "... affected resource {} has type {}, title '{}'"\
                              .format(resource.short_id, resource.resource_type,
                                      resource.title)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)

        else:  # check all resources
            print("LOOKING FOR UNREGISTERED FILES FOR ALL RESOURCES")
            for r in BaseResource.objects.all():
                # Pabitra: Not sure why are we skipping other resource types
                # Alva: cannot preserve file integrity constraints for other file types.
                if r.resource_type == 'CompositeResource':
                    print("LOOKING FOR UNREGISTERED FILES FOR RESOURCE {} (current files {})"
                          .format(r.short_id, str(r.files.all().count())))
                    try:
                        # get the typed resource
                        resource = r.get_content_model()
                    except Exception as e:
                        msg = "resource {} has no proxy resource: {}"\
                              .format(r.short_id, e.value)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)
                        msg = "... affected resource {} has type {}, title '{}'"\
                              .format(r.short_id, r.resource_type, r.title)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)
                        continue  # next resource

                    _, count = ingest_s3_files(resource,
                                                  logger,
                                                  stop_on_error=False,
                                                  echo_errors=not options['log'],
                                                  log_errors=options['log'],
                                                  return_errors=False)
                    if count:
                        msg = "... affected resource {} has type {}, title '{}'"\
                              .format(resource.short_id, resource.resource_type, resource.title)
                        if log_errors:
                            logger.info(msg)
                        if echo_errors:
                            print(msg)

                else:
                    print("resource {} has type {}: skipping".format(r.short_id, r.resource_type))
