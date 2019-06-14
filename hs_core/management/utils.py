# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django

This checks that every file in IRODS corresponds to a ResourceFile in Django.
If a file in iRODS is not present in Django, it attempts to register that file in Django.

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

import json

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException
from hs_file_types.utils import set_logical_file_type, get_logical_file_type

from requests import post

from hs_core.models import BaseResource
from hs_core.hydroshare import get_resource_by_shortkey
from hs_core.views.utils import link_irods_file_to_django

import logging


def check_relations(resource):
    """Check for dangling relations due to deleted resource files.

    :param resource: resource to check
    """
    for r in resource.metadata.relations.all():
        if r.value.startswith('http://www.hydroshare.org/resource/'):
            target = r.value[len('http://www.hydroshare.org/resource/'):].rstrip('/')
            try:
                get_resource_by_shortkey(target, or_404=False)
            except BaseResource.DoesNotExist:
                print("relation {} {} {} (this does not exist)"
                      .format(resource.short_id, r.type, target))


def check_irods_files(resource, stop_on_error=False, log_errors=True,
                      echo_errors=False, return_errors=False,
                      sync_ispublic=False, clean_irods=False, clean_django=False):
    """Check whether files in resource.files and on iRODS agree.

    :param resource: resource to check
    :param stop_on_error: whether to raise a ValidationError exception on first error
    :param log_errors: whether to log errors to Django log
    :param echo_errors: whether to print errors on stdout
    :param return_errors: whether to collect errors in an array and return them.
    :param sync_ispublic: whether to repair deviations between ResourceAccess.public
           and AVU isPublic
    :param clean_irods: whether to delete files in iRODs that are not in Django
    :param clean_django: whether to delete files in Django that are not in iRODs
    """
    from hs_core.hydroshare.resource import delete_resource_file

    logger = logging.getLogger(__name__)
    istorage = resource.get_irods_storage()
    errors = []
    ecount = 0

    # skip federated resources if not configured to handle these
    if resource.is_federated and not settings.REMOTE_USE_IRODS:
        msg = "check_irods_files: skipping check of federated resource {} in unfederated mode"\
            .format(resource.short_id)
        if echo_errors:
            print(msg)
        if log_errors:
            logger.info(msg)

    # skip resources that do not exist in iRODS
    elif not istorage.exists(resource.root_path):
            msg = "root path {} does not exist in iRODS".format(resource.root_path)
            ecount += 1
            if echo_errors:
                print(msg)
            if log_errors:
                logger.error(msg)
            if return_errors:
                errors.append(msg)

    else:
        # Step 2: does every file in Django refer to an existing file in iRODS?
        for f in resource.files.all():
            if not istorage.exists(f.storage_path):
                ecount += 1
                msg = "check_irods_files: django file {} does not exist in iRODS"\
                    .format(f.storage_path)
                if clean_django:
                    delete_resource_file(resource.short_id, f.short_path, resource.creator,
                                         delete_logical_file=False)
                    msg += " (DELETED FROM DJANGO)"
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)

        # Step 3: for composite resources, does every composite metadata file exist?
        from hs_composite_resource.models import CompositeResource as CR
        if isinstance(resource, CR):
            for lf in resource.logical_files:
                if not istorage.exists(lf.metadata_file_path):
                    ecount += 1
                    msg = "check_irods_files: logical metadata file {} does not exist in iRODS"\
                        .format(lf.metadata_file_path)
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    if return_errors:
                        errors.append(msg)
                    if stop_on_error:
                        raise ValidationError(msg)
                if not istorage.exists(lf.map_file_path):
                    ecount += 1
                    msg = "check_irods_files: logical map file {} does not exist in iRODS"\
                        .format(lf.map_file_path)
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    if return_errors:
                        errors.append(msg)
                    if stop_on_error:
                        raise ValidationError(msg)

        # Step 4: does every iRODS file correspond to a record in files?
        error2, ecount2 = __check_irods_directory(resource, resource.file_path, logger,
                                                  stop_on_error=stop_on_error,
                                                  log_errors=log_errors,
                                                  echo_errors=echo_errors,
                                                  return_errors=return_errors,
                                                  clean=clean_irods)
        errors.extend(error2)
        ecount += ecount2

        # Step 5: check whether the iRODS public flag agrees with Django
        django_public = resource.raccess.public
        irods_public = None
        try:
            irods_public = resource.getAVU('isPublic')
        except SessionException as ex:
            msg = "cannot read isPublic attribute of {}: {}"\
                .format(resource.short_id, ex.stderr)
            ecount += 1
            if log_errors:
                logger.error(msg)
            if echo_errors:
                print(msg)
            if return_errors:
                errors.append(msg)
            if stop_on_error:
                raise ValidationError(msg)

        if irods_public is not None:
            # convert to boolean
            irods_public = str(irods_public).lower() == 'true'

        if irods_public is None or irods_public != django_public:
            ecount += 1
            if not django_public:  # and irods_public
                msg = "check_irods_files: resource {} public in irods, private in Django"\
                    .format(resource.short_id)
                if sync_ispublic:
                    try:
                        resource.setAVU('isPublic', 'false')
                        msg += " (REPAIRED IN IRODS)"
                    except SessionException as ex:
                        msg += ": (CANNOT REPAIR: {})"\
                            .format(ex.stderr)

            else:  # django_public and not irods_public
                msg = "check_irods_files: resource {} private in irods, public in Django"\
                    .format(resource.short_id)
                if sync_ispublic:
                    try:
                        resource.setAVU('isPublic', 'true')
                        msg += " (REPAIRED IN IRODS)"
                    except SessionException as ex:
                        msg += ": (CANNOT REPAIR: {})"\
                            .format(ex.stderr)

            if msg != '':
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)

    if ecount > 0:  # print information about the affected resource (not really an error)
        msg = "check_irods_files: affected resource {} type is {}, title is '{}'"\
            .format(resource.short_id, resource.resource_type,
                    resource.title.encode('ascii', 'replace'))
        if log_errors:
            logger.error(msg)
        if echo_errors:
            print(msg)
        if return_errors:
            errors.append(msg)

    return errors, ecount  # empty unless return_errors=True


def __check_irods_directory(resource, dir, logger,
                            stop_on_error=False, log_errors=True,
                            echo_errors=False, return_errors=False,
                            clean=False):
    """List a directory and check files there for conformance with django ResourceFiles.

    :param stop_on_error: whether to raise a ValidationError exception on first error
    :param log_errors: whether to log errors to Django log
    :param echo_errors: whether to print errors on stdout
    :param return_errors: whether to collect errors in an array and return them.

    """
    errors = []
    ecount = 0
    istorage = resource.get_irods_storage()
    try:
        listing = istorage.listdir(dir)
        for fname in listing[1]:  # files
            # do not use os.path.join because fname might contain unicode characters
            fullpath = dir + '/' + fname
            found = False
            for f in resource.files.all():
                if f.storage_path == fullpath:
                    found = True
                    break
            if not found and not resource.is_aggregation_xml_file(fullpath):
                ecount += 1
                msg = "check_irods_files: file {} in iRODs does not exist in Django"\
                    .format(fullpath.encode('ascii', 'replace'))
                if clean:
                    try:
                        istorage.delete(fullpath)
                        msg += " (DELETED FROM IRODS)"
                    except SessionException as ex:
                        msg += ": (CANNOT DELETE: {})"\
                            .format(ex.stderr)
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)

        for dname in listing[0]:  # directories
            # do not use os.path.join because paths might contain unicode characters!
            error2, ecount2 = __check_irods_directory(resource, dir + '/' + dname, logger,
                                                      stop_on_error=stop_on_error,
                                                      echo_errors=echo_errors,
                                                      log_errors=log_errors,
                                                      return_errors=return_errors,
                                                      clean=clean)
            errors.extend(error2)
            ecount += ecount2

    except SessionException:
        pass  # not an error not to have a file directory.
        # Non-existence of files is checked elsewhere.

    return errors, ecount  # empty unless return_errors=True


def ingest_irods_files(resource,
                       logger,
                       stop_on_error=False,
                       echo_errors=True,
                       log_errors=False,
                       return_errors=False):

    istorage = resource.get_irods_storage()
    errors = []
    ecount = 0

    # skip federated resources if not configured to handle these
    if resource.is_federated and not settings.REMOTE_USE_IRODS:
        msg = "ingest_irods_files: skipping ingest of federated resource {} in unfederated mode"\
            .format(resource.short_id)
        if echo_errors:
            print(msg)
        if log_errors:
            logger.info(msg)

    else:
        # flag non-existent resources in iRODS
        if not istorage.exists(resource.root_path):
            msg = "root path {} does not exist in iRODS".format(resource.root_path)
            ecount += 1
            if echo_errors:
                print(msg)
            if log_errors:
                logger.error(msg)
            if return_errors:
                errors.append(msg)

        # flag non-existent file paths in iRODS
        elif not istorage.exists(resource.file_path):
            msg = "file path {} does not exist in iRODS".format(resource.file_path)
            ecount += 1
            if echo_errors:
                print(msg)
            if log_errors:
                logger.error(msg)
            if return_errors:
                errors.append(msg)

        else:
            return __ingest_irods_directory(resource,
                                            resource.file_path,
                                            logger,
                                            stop_on_error=False,
                                            echo_errors=True,
                                            log_errors=False,
                                            return_errors=False)

    return errors, ecount


def __ingest_irods_directory(resource,
                             dir,
                             logger,
                             stop_on_error=False,
                             log_errors=True,
                             echo_errors=False,
                             return_errors=False):
    """
    list a directory and ingest files there for conformance with django ResourceFiles

    :param stop_on_error: whether to raise a ValidationError exception on first error
    :param log_errors: whether to log errors to Django log
    :param echo_errors: whether to print errors on stdout
    :param return_errors: whether to collect errors in an array and return them.

    """
    errors = []
    ecount = 0
    istorage = resource.get_irods_storage()
    try:
        listing = istorage.listdir(dir)
        for fname in listing[1]:  # files
            # do not use os.path.join because fname might contain unicode characters
            fullpath = dir + '/' + fname
            found = False
            for res_file in resource.files.all():
                if res_file.storage_path == fullpath:
                    found = True

            if not found and not resource.is_aggregation_xml_file(fullpath):
                ecount += 1
                msg = "ingest_irods_files: file {} in iRODs does not exist in Django (INGESTING)"\
                    .format(fullpath.encode('ascii', 'replace'))
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)
                # TODO: does not ingest logical file structure for composite resources
                link_irods_file_to_django(resource, fullpath)

                # Create required logical files as necessary
                if resource.resource_type == "CompositeResource":
                    file_type = get_logical_file_type(res=resource, user=None,
                                                      file_id=res_file.pk, fail_feedback=False)
                    if not res_file.has_logical_file and file_type is not None:
                        msg = "ingest_irods_files: setting required logical file for {}"\
                              .format(fullpath)
                        if echo_errors:
                            print(msg)
                        if log_errors:
                            logger.error(msg)
                        if return_errors:
                            errors.append(msg)
                        if stop_on_error:
                            raise ValidationError(msg)
                        set_logical_file_type(res=resource, user=None, file_id=res_file.pk,
                                              fail_feedback=False)
                    elif res_file.has_logical_file and file_type is not None and \
                            not isinstance(res_file.logical_file, file_type):
                        msg = "ingest_irods_files: logical file for {} has type {}, should be {}"\
                            .format(res_file.storage_path.encode('ascii', 'replace'),
                                    type(res_file.logical_file).__name__,
                                    file_type.__name__)
                        if echo_errors:
                            print(msg)
                        if log_errors:
                            logger.error(msg)
                        if return_errors:
                            errors.append(msg)
                        if stop_on_error:
                            raise ValidationError(msg)
                    elif res_file.has_logical_file and file_type is None:
                        msg = "ingest_irods_files: logical file for {} has type {}, not needed"\
                            .format(res_file.storage_path, type(res_file.logical_file).__name__,
                                    file_type.__name__)
                        if echo_errors:
                            print(msg)
                        if log_errors:
                            logger.error(msg)
                        if return_errors:
                            errors.append(msg)
                        if stop_on_error:
                            raise ValidationError(msg)

        for dname in listing[0]:  # directories
            # do not use os.path.join because fname might contain unicode characters
            error2, ecount2 = __ingest_irods_directory(resource,
                                                       dir + '/' + dname,
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
    """ This checks for resource trees in iRODS with no correspondence to Django at all

    :param log_errors: whether to log errors to Django log
    :param echo_errors: whether to print errors on stdout
    :param return_errors: whether to collect errors in an array and return them.
    """

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


class CheckJSONLD(object):
    def __init__(self, short_id):
        self.short_id = short_id

    def test(self):
        default_site = Site.objects.first()
        validator_url = "https://search.google.com/structured-data/testing-tool/validate"
        url = "https://" + default_site.domain + "/resource/" + self.short_id
        cookies = {"NID": settings.GOOGLE_COOKIE_HASH}

        response = post(validator_url, {"url": url}, cookies=cookies)

        response_json = json.loads(response.text[4:])
        if response_json.get("totalNumErrors") > 0:
            for error in response_json.get("errors"):
                if "includedInDataCatalog" not in error.get('args'):
                    errors = response_json.get("errors")
                    print("Error found on resource {}: {}".format(self.short_id, errors))
                    return

        if response_json.get("totalNumWarnings") > 0:
            warnings = response_json.get("warnings")
            print("Warnings found on resource {}: {}".format(self.short_id, warnings))
            return


def repair_resource(resource, logger, stop_on_error=False,
                    log_errors=True, echo_errors=False, return_errors=False):
    errors = []
    ecount = 0

    try:
        resource = get_resource_by_shortkey(resource.short_id, or_404=False)
    except BaseResource.DoesNotExist:
        msg = "Resource with id {} not found in Django Resources".format(resource.short_id)
        if log_errors:
            logger.error(msg)
        if echo_errors:
            print(msg)
        if return_errors:
            errors.append(msg)
            ecount = ecount + 1
        return errors, ecount

    print("REPAIRING RESOURCE {}".format(resource.short_id))

    # ingest any dangling iRODS files that you can
    # Do this before check because otherwise, errors get printed twice
    # TODO: This does not currently work properly for composite resources
    # if resource.resource_type == 'CompositeResource' or \
    if resource.resource_type == 'GenericResource' or \
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
                  .format(resource.short_id, resource.resource_type,
                          resource.title.encode('ascii', 'replace')))

    _, count = check_irods_files(resource,
                                 stop_on_error=False,
                                 echo_errors=True,
                                 log_errors=False,
                                 return_errors=False,
                                 clean_irods=False,
                                 clean_django=True,
                                 sync_ispublic=True)
    if count:
        print("... affected resource {} has type {}, title '{}'"
              .format(resource.short_id, resource.resource_type,
                      resource.title.encode('ascii', 'replace')))


class CheckResource(object):
    """ comprehensively check a resource """
    header = False

    def __init__(self, short_id):
        self.short_id = short_id

    def label(self):
        if not self.header:
            print("resource {}:".format(self.resource.short_id))
            self.header = True

    def check_avu(self, label):
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
            self.resource = get_resource_by_shortkey(self.short_id, or_404=False)
        except BaseResource.DoesNotExist:
            print("{} does not exist in Django".format(self.short_id))
            return

        # skip federated resources if not configured to handle these
        if self.resource.is_federated and not settings.REMOTE_USE_IRODS:
            msg = "check_resource: skipping check of federated resource {} in unfederated mode"\
                .format(self.resource.short_id)
            print(msg)

        istorage = self.resource.get_irods_storage()

        if not istorage.exists(self.resource.root_path):
            self.label()
            print("  root path {} does not exist in iRODS".format(self.resource.root_path))
            print("  ... resource {} has type {} and title {}"
                  .format(self.resource.short_id,
                          self.resource.resource_type,
                          self.resource.title.encode('ascii', 'replace')))
            return

        for a in ('bag_modified', 'isPublic', 'resourceType', 'quotaUserName'):
            value = self.check_avu(a)
            if a == 'resourceType' and value is not None and value != self.resource.resource_type:
                self.label()
                print("  AVU resourceType is {}, should be {}".format(value.encode('ascii',
                                                                                   'replace'),
                                                                      self.resource.resource_type))
            if a == 'isPublic' and value is not None and value != self.resource.raccess.public:
                self.label()
                print("  AVU isPublic is {}, but public is {}".format(value.encode('ascii',
                                                                                   'replace'),
                                                                      self.resource.raccess.public))

        irods_issues, irods_errors = check_irods_files(self.resource,
                                                       log_errors=False,
                                                       echo_errors=False,
                                                       return_errors=True)

        if irods_errors:
            self.label()
            print("  iRODS errors:")
            for e in irods_issues:
                print("    {}".format(e))

        if self.resource.resource_type == 'CompositeResource':
            logical_issues = []
            for res_file in self.resource.files.all():
                file_type = get_logical_file_type(res=self.resource, user=None,
                                                  file_id=res_file.pk, fail_feedback=False)
                if not res_file.has_logical_file and file_type is not None:
                    msg = "check_resource: file {} does not have required logical file {}"\
                          .format(res_file.storage_path.encode('ascii', 'replace'),
                                  file_type.__name__)
                    logical_issues.append(msg)
                elif res_file.has_logical_file and file_type is None:
                    msg = "check_resource: logical file for {} has type {}, not needed"\
                          .format(res_file.storage_path.encode('ascii', 'replace'),
                                  type(res_file.logical_file).__name__)
                    logical_issues.append(msg)
                elif res_file.has_logical_file and file_type is not None and \
                        not isinstance(res_file.logical_file, file_type):
                    msg = "check_resource: logical file for {} has type {}, should be {}"\
                          .format(res_file.storage_path.encode('ascii', 'replace'),
                                  type(res_file.logical_file).__name__,
                                  file_type.__name__)
                    logical_issues.append(msg)

            if logical_issues:
                self.label()
                print("  Logical file errors:")
                for e in logical_issues:
                    print("    {}".format(e))
