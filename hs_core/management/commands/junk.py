# -*- coding: utf-8 -*-

"""
Test whether irods is corrupting output from icommands
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django_irods.icommands import SessionException

# import logging
# from django_irods.storage import IrodsStorage


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


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

                istorage = resource.get_irods_storage()
                for avu in ('bag_modified', 'isPublic', 'metadata_dirty',
                            'quotaUserName', 'resourceType'):
                    try:
                        value = istorage.getAVU(resource.root_path, avu)
                    except SessionException as s:
                        msg = "Resource with id {} has no {} AVU: {}"\
                              .format(resource.short_id, avu, s.message)
                    print(msg)
                    continue

                    if not is_ascii(value):
                        print("{} AVU {} has non-ascii characters {}"
                              .format(resource.short_id, avu, value.encode('ascii', 'replace')))
                    else:
                        print("{} AVU {} is {}".format(resource.short_id, avu, value))

        else:  # check all resources
            for r in BaseResource.objects.all():
                try:
                    resource = get_resource_by_shortkey(r.short_id, or_404=False)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(r.short_id)
                    print(msg)
                    continue

                istorage = resource.get_irods_storage()
                for avu in ('bag_modified', 'isPublic', 'metadata_dirty',
                            'quotaUserName', 'resourceType'):
                    try:
                        value = istorage.getAVU(resource.root_path, avu)
                    except SessionException as s:
                        msg = "Resource with id {} has no {} attribute: {}"\
                              .format(resource.short_id, avu, s.message)
                        print(msg)
                        continue
                    if not is_ascii(value):
                        print("{} AVU {}lic has non-ascii characters {}"
                              .format(resource.short_id, avu, value.encode('ascii', 'replace')))
                    else:
                        print("{} AVU {} is {}".format(resource.short_id, avu, value))
