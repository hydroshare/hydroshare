"""This prints the state of a logical file.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource, ResourceFile
from django_irods.icommands import SessionException
from django.core.exceptions import ValidationError
import os
import logging


def __check_irods_directory(self, dir, expected, logger,
                            stop_on_error=False, log_errors=True,
                            echo_errors=False, return_errors=False,
                            clean=False):
    """List a directory and check files there for conformance with django ResourceFiles.

    :param dir: directory to list.
    :param expected: set of filenames to expect.
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
            if fullpath not in expected:
                ecount += 1
                msg = "check_irods_files: file {} in iRODs does not exist in Django"\
                    .format(fullpath)
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
            error2, ecount2 = __check_irods_directory(self, os.path.join(dir, dname), expected,
                                                      logger,
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


def debug_resource(short_id):
    """ Debug view for resource depicts output of various integrity checking scripts """

    try:
        res = BaseResource.objects.get(short_id=short_id)
    except BaseResource.DoesNotExist:
        print("{} does not exist".format(short_id))

    resource = res.get_content_model()
    assert resource, (res, res.content_model)

    logger = logging.getLogger(__name__)
    if resource.resource_type == 'CompositeResource':
        storage = resource.get_irods_storage()
        resource.create_aggregation_xml_documents()
        print("resource {}".format(resource.short_id))
        expected_files = set()
        for l in resource.logical_files:
            # print("{} {}".format(l.resource.short_id, l.metadata_file_path))
            # print("{} {}".format(l.resource.short_id, l.map_file_path))
            expected_files.add(l.metadata_file_path)
            expected_files.add(l.map_file_path)
        for f in ResourceFile.objects.filter(object_id=resource.id):
            # print("{} {}".format(f.resource.short_id, f.storage_path))
            expected_files.add(f.storage_path)
        for e in expected_files:
            if not storage.exists(e):
                print("    {} does not exist in irods".format(e))
        __check_irods_directory(resource, resource.root_path + "/data/contents",
                                expected_files, logger)


class Command(BaseCommand):
    help = "Print debugging information about logical files."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

        # Named (optional) arguments
        parser.add_argument(
            '--log',
            action='store_true',  # True for presence, False for absence
            dest='log',           # value is options['log']
            help='log errors to system log',
        )

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                debug_resource(rid)
        else:
            for r in BaseResource.objects.filter(resource_type="CompositeResource"):
                debug_resource(r.short_id)

            print("No resources to check.")
