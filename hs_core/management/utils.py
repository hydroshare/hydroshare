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
from django.core.exceptions import ValidationError
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException
from hs_core.models import BaseResource
from hs_core.hydroshare import get_resource_by_shortkey
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


def check_for_dangling_irods(echo_errors=True, log_errors=False, return_errors=False):
    """ This checks for resource trees in iRODS with no correspondence to Django at all """

    istorage = IrodsStorage()  # local only
    toplevel = istorage.listdir('.')  # list the resources themselves
    logger = logging.getLogger(__name__)

    errors = []
    for id in toplevel[0]:  # directories
        try:
            get_resource_by_shortkey(id, or_404=False)
        except BaseResource.DoesNotExist:
            msg = "resource {} does not exist in Django".format(id)
            if echo_errors:
                print(msg)
            if log_errors:
                logger.error(msg)
            if return_errors:
                errors.append(msg)
    return errors


class TestResource(object):
    header = False

    def __init__(self, short_id):
        self.short_id = short_id

    def label(self):
        if not self.header:
            print("resource {}:".format(self.resource.short_id))
            self.header = True

    def test_avu(self, label):
        try:
            value = self.resource.getAVU(label)
            if value is None:
                self.label()
                print("  AVU {} is None".format(label))
            return value
        except SessionException:
            self.label()
            print("  AVU {} NOT FOUND.".format(label))
            return None

    def test(self):
        """ Test view for resource depicts output of various integrity checking scripts """

        # print("TESTING {}".format(self.short_id))  # leave this for debugging

        try:
            res = BaseResource.objects.get(short_id=self.short_id)
        except BaseResource.DoesNotExist:
            print("{} does not exist in Django".format(self.short_id))

        self.resource = res.get_content_model()
        assert self.resource, (res, res.content_model)

        # skip federated resources if not configured to handle these
        if self.resource.is_federated and not settings.REMOTE_USE_IRODS:
            msg = "test_resource: skipping check of federated resource {} in unfederated mode"\
                .format(self.resource.short_id)
            print(msg)

        istorage = self.resource.get_irods_storage()

        if not istorage.exists(self.resource.root_path):
            self.label()
            print("  root path {} does not exist in iRODS".format(self.resource.root_path))
            return

        for a in ('bag_modified', 'isPublic', 'resourceType', 'quotaUserName'):
            value = self.test_avu(a)
            if a == 'resourceType' and value is not None and value != self.resource.resource_type:
                self.label()
                print("  AVU resourceType is {}, should be {}".format(value,
                                                                      self.resource.resource_type))
            if a == 'isPublic' and value is not None and value != self.resource.raccess.public:
                self.label()
                print("  AVU isPublic is {}, but public is {}".format(value,
                                                                      self.resource.raccess.public))

        irods_issues, irods_errors = self.resource.check_irods_files(log_errors=False,
                                                                     return_errors=True)

        if irods_errors:
            self.label()
            print("  iRODS errors:")
            for e in irods_issues:
                print("    {}".format(e))

        logical_header = False

        if self.resource.resource_type == 'CompositeResource':
            for res_file in self.resource.files.all():
                if not res_file.has_logical_file:
                    self.label()
                    if not logical_header:
                        print("  logical file errors:")
                    print("    {} logical file NOT SPECIFIED".format(res_file.short_path))
