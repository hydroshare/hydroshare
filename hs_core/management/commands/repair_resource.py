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

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    res = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)

                resource = res.get_content_model()

                print("REPAIRING RESOURCE {}".format(rid))
                resource.check_irods_files(stop_on_error=False,
                                           echo_errors=True,
                                           log_errors=False,
                                           return_errors=False,
                                           clean_irods=False,
                                           clean_django=True,
                                           sync_ispublic=True)
                if resource.resource_type == 'CompositeResource' or \
                   resource.resource_type == 'GenericResource' or \
                   resource.resource_type == 'ModelInstanceResource' or \
                   resource.resource_type == 'ModelProgramResource':
                    logger = logging.getLogger(__name__)
                    ingest_irods_files(resource,
                                       logger,
                                       stop_on_error=False,
                                       echo_errors=True,
                                       log_errors=False,
                                       return_errors=False)

            if resource.resource_type == 'CompositeResource':
                for res_file in resource.files.all():
                    if not res_file.has_logical_file:
                        print("Logical file missing for file {}".format(res_file.short_path))
                resource.set_default_logical_file()

        else:  # check all resources
            print("REPAIRING ALL RESOURCES")
            for r in BaseResource.objects.all():
                resource = r.get_content_model()

                # first clean up Django references to non-existent iRODS files
                resource.check_irods_files(stop_on_error=False,
                                           echo_errors=True,
                                           log_errors=False,
                                           return_errors=False,
                                           clean_irods=False,
                                           clean_django=True,
                                           sync_ispublic=True)

                # now ingest any dangling iRODS files that you can
                if resource.resource_type == 'CompositeResource' or \
                   resource.resource_type == 'GenericResource' or \
                   resource.resource_type == 'ModelInstanceResource' or \
                   resource.resource_type == 'ModelProgramResource':
                    logger = logging.getLogger(__name__)
                    ingest_irods_files(resource,
                                       logger,
                                       stop_on_error=False,
                                       echo_errors=True,
                                       log_errors=False,
                                       return_errors=False)

                if resource.resource_type == 'CompositeResource':
                    for res_file in resource.files.all():
                        if not res_file.has_logical_file:
                            print("Logical file missing for file {}".format(res_file.short_path))
                    resource.set_default_logical_file()
