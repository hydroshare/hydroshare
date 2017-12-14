# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that every file in IRODS corresponds to a ResourceFile in Django.
If a file in iRODS is not present in Django, it attempts to register that file in Django.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource

from hs_core.management.utils import ingest_irods_files


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

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)
                    continue

                # Pabitra: Not sure why are we skipping other resource types
                if resource.resource_type != 'CompositeResource' and \
                   resource.resource_type != 'GenericResource' and \
                   resource.resource_type != 'ModelInstanceResource' and \
                   resource.resource_type != 'ModelProgramResource':
                    print("resource {} has type {}: skipping".format(resource.short_id,
                                                                     resource.resource_type))
                else:
                    print("LOOKING FOR UNREGISTERED IRODS FILES FOR RESOURCE {} (current files {})"
                          .format(rid, str(resource.files.all().count())))
                    # get the typed resource
                    resource = resource.get_content_model()
                    ingest_irods_files(resource,
                                       logger,
                                       stop_on_error=False,
                                       echo_errors=not options['log'],
                                       log_errors=options['log'],
                                       return_errors=False)

        else:  # check all resources
            print("LOOKING FOR UNREGISTERED IRODS FILES FOR ALL RESOURCES")
            for r in BaseResource.objects.all():
                # Pabitra: Not sure why are we skipping other resource types
                if r.resource_type == 'CompositeResource' or \
                   r.resource_type == 'GenericResource' or \
                   r.resource_type == 'ModelInstanceResource' or \
                   r.resource_type == 'ModelProgramResource':
                    print("LOOKING FOR UNREGISTERED IRODS FILES FOR RESOURCE {} (current files {})"
                          .format(r.short_id, str(r.files.all().count())))
                    # get the typed resource
                    r = r.get_content_model()
                    ingest_irods_files(r,
                                       logger,
                                       stop_on_error=False,
                                       echo_errors=not options['log'],
                                       log_errors=options['log'],
                                       return_errors=False)
                else:
                    print("resource {} has type {}: skipping".format(r.short_id, r.resource_type))
