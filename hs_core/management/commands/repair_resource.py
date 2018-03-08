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
from hs_core.management.utils import ingest_irods_files

import logging


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

    def handle(self, *args, **options):

        log_errors = options['log']
        echo_errors = not options['log']
        logger = logging.getLogger(__name__)

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    r = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    if log_errors:
                        logger.error(msg)
                    if echo_errors:
                        print(msg)
                    continue  # next resource

                try:
                    resource = r.get_content_model()
                except Exception as e:
                    msg = "resource {} has no proxy class: {}"\
                          .format(r.short_id, e.value)
                    if log_errors:
                        logger.error(msg)
                    if echo_errors:
                        print(msg)
                    msg = "... affected resource {} has type {}, title '{}'"\
                          .format(r.short_id, r.resource_type, r.title)
                    if log_errors:
                        logger.info(msg)
                    if echo_errors:
                        print(msg)
                    continue  # next resource

                print("REPAIRING RESOURCE {}".format(rid))

                # ingest any dangling iRODS files that you can
                # Do this before check because otherwise, errors get printed twice
                if resource.resource_type == 'CompositeResource' or \
                   resource.resource_type == 'GenericResource' or \
                   resource.resource_type == 'ModelInstanceResource' or \
                   resource.resource_type == 'ModelProgramResource':
                    _, count = ingest_irods_files(resource,
                                                  logger,
                                                  stop_on_error=False,
                                                  echo_errors=True,
                                                  log_errors=False,
                                                  return_errors=False)
                    if count:
                        print("... affected resource {} has type {}, title '{}'"
                              .format(resource.short_id, resource.resource_type, resource.title))
                _, count = resource.check_irods_files(stop_on_error=False,
                                                      echo_errors=True,
                                                      log_errors=False,
                                                      return_errors=False,
                                                      clean_irods=False,
                                                      clean_django=True,
                                                      sync_ispublic=True)
                if count:
                    print("... affected resource {} has type {}, title '{}'"
                          .format(resource.short_id, resource.resource_type, resource.title))

            if resource.resource_type == 'CompositeResource':
                count = 0
                for res_file in resource.files.all():
                    if not res_file.has_logical_file:
                        count += 1
                        print("Logical file missing for file {} (CREATING)"
                              .format(res_file.short_path))
                resource.set_default_logical_file()
            if count:
                print("... affected resource {} has type {}, title '{}'"
                      .format(resource.short_id, resource.resource_type, resource.title))

        else:  # check all resources
            print("REPAIRING ALL RESOURCES")
            for r in BaseResource.objects.all():
                try:
                    resource = r.get_content_model()
                except Exception as e:
                    msg = "resource {} has no proxy class: {}".format(r.short_id, e.value)
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    msg = "... affected resource {} has type {}, title '{}'"\
                          .format(r.short_id, r.resource_type, r.title)
                    if log_errors:
                        logger.info(msg)
                    if echo_errors:
                        print(msg)
                    continue  # next resource

                # ingest any dangling iRODS files that you can
                # Do this before check because otherwise, errors get printed twice
                if resource.resource_type == 'CompositeResource' or \
                   resource.resource_type == 'GenericResource' or \
                   resource.resource_type == 'ModelInstanceResource' or \
                   resource.resource_type == 'ModelProgramResource':
                    _, count = ingest_irods_files(resource,
                                                  logger,
                                                  stop_on_error=False,
                                                  echo_errors=True,
                                                  log_errors=False,
                                                  return_errors=False)
                    if count:
                        print("... affected resource {} has type {}, title '{}'"
                              .format(resource.short_id, resource.resource_type, resource.title))

                # clean up Django references to non-existent iRODS files
                _, count = resource.check_irods_files(stop_on_error=False,
                                                      echo_errors=True,
                                                      log_errors=False,
                                                      return_errors=False,
                                                      clean_irods=False,
                                                      clean_django=True,
                                                      sync_ispublic=True)
                if count:
                    print("... affected resource {} has type {}, title '{}'"
                          .format(resource.short_id, resource.resource_type, resource.title))

                # create missing logical files
                if resource.resource_type == 'CompositeResource':
                    count = 0
                    for res_file in resource.files.all():
                        if not res_file.has_logical_file:
                            count += 1
                            print("Resource {}: logical file missing for file {} (CREATING)"
                                  .format(resource.short_id, res_file.short_path))
                    resource.set_default_logical_file()

                if count:
                    print("... affected resource {} has type {}, title '{}'"
                          .format(resource.short_id, resource.resource_type, resource.title))
