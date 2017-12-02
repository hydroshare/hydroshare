# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that every file in IRODS corresponds to a ResourceFile in Django.
If a file in iRODS is not present in Django, it attempts to register that file in Django.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django_irods.icommands import SessionException
from hs_core.models import BaseResource

from hs_core.views.utils import link_irods_file_to_django


import logging


def ingest_irods_files(self,
                       logger,
                       stop_on_error=False,
                       echo_errors=True,
                       log_errors=False,
                       return_errors=False):

    istorage = self.get_irods_storage()
    errors = []
    ecount = 0

    # skip federated resources if not configured to handle these
    if self.is_federated and not settings.REMOTE_USE_IRODS:
        msg = "check_irods_files: skipping check of federated resource {} in unfederated mode"\
            .format(self.short_id)
        if echo_errors:
            print(msg)
        if log_errors:
            logger.info(msg)

    # flag non-existent resources in iRODS
    else:
        if not istorage.exists(self.root_path):
            msg = "root path {} does not exist in iRODS".format(self.root_path)
            ecount += 1
            if echo_errors:
                print(msg)
            if log_errors:
                logger.error(msg)
            if return_errors:
                errors.append(msg)

        else:
            return __ingest_irods_directory(self,
                                            self.file_path,
                                            logger,
                                            stop_on_error=False,
                                            echo_errors=True,
                                            log_errors=False,
                                            return_errors=False)

    return errors, ecount


def __ingest_irods_directory(self,
                             dir,
                             logger,
                             stop_on_error=False,
                             log_errors=True,
                             echo_errors=False,
                             return_errors=False):
    """
    list a directory and check files there for conformance with django ResourceFiles

    :param stop_on_error: whether to raise a ValidationError exception on first error
    :param log_errors: whether to log errors to Django log
    :param echo_errors: whether to print errors on stdout
    :param return_errors: whether to collect errors in an array and return them.

    """
    errors = []
    ecount = 0
    istorage = self.get_irods_storage()
    try:
        listing = istorage.listdir(dir)
        for fname in listing[1]:  # files
            fullpath = os.path.join(dir, fname)
            found = False
            for f in self.files.all():
                if f.storage_path == fullpath:
                    found = True
                    break
            if not found:
                ecount += 1
                msg = "ingest_irods_files: file {} in iRODs does not exist in Django (INGESTING)"\
                    .format(fullpath)
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)
                # TODO: only works properly for generic and composite resources!
                link_irods_file_to_django(self, fullpath)

        for dname in listing[0]:  # directories
            error2, ecount2 = __ingest_irods_directory(self,
                                                       os.path.join(dir, dname),
                                                       logger,
                                                       stop_on_error=stop_on_error,
                                                       echo_errors=echo_errors,
                                                       log_errors=log_errors,
                                                       return_errors=return_errors)
            errors.extend(error2)
            ecount += ecount2

    except SessionException as se:
        print("iRODs error: {}".format(se.stderr))
        logger.error("iRODs error: {}".format(se.stderr))

    return errors, ecount  # empty unless return_errors=True


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
                   resource.resource_type != 'GenericResource':
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
                   r.resource_type == 'GenericResource':
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
