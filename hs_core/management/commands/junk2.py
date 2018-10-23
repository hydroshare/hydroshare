# -*- coding: utf-8 -*-

"""
Test whether irods is corrupting output from icommands
"""

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_text
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django_irods.icommands import SessionException
import os

# import logging
# from django_irods.storage import IrodsStorage


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def check_irods_directory(self, dir):
    """List a directory and check filenames for illegal characters

    :param dir: directory to list.
    """
    istorage = self.get_irods_storage()
    try:
        listing = istorage.listdir(dir)
        for fname in listing[1]:  # files
            if not is_ascii(fname):
                encoded = fname.encode('string-escape') 
                print("{}: file name {} contains non-ascii characters"
                      .format(self.short_id, encoded))
                continue

        for dname in listing[0]:  # directories
            if not is_ascii(dname):
                encoded = fname.encode('string-escape') 
                print("{}: directory name {} contains non-ascii characters"
                      .format(self.short_id, encoded))
                continue

            check_irods_directory(self, os.path.join(dir, dname))

    except SessionException as s:
        print("{}: session exception {}".format(self.short_id, s.stderr))


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(rid, or_404=False)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)
                    continue

                check_irods_directory(resource, resource.root_path)

        else:  # check all resources
            for r in BaseResource.objects.all():
                try:
                    resource = get_resource_by_shortkey(r.short_id, or_404=False)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(r.short_id)
                    print(msg)
                    continue

                check_irods_directory(resource, resource.root_path)
