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
from hs_core.hydroshare.utils import get_resource_by_shortkey
from django_irods.storage import IrodsStorage

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
            help='log actions to system log',
        )

    def handle(self, *args, **options):

        defaultpath = '/hydroshareuserZone/home/localHydroProxy'
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                except BaseResource.DoesNotExist:
                    msg = "Resource with id {} not found in Django Resources".format(rid)
                    print(msg)

                if resource.resource_federation_path == defaultpath:
                    print("REMAPPING RESOURCE {} TO LOCAL USERSPACE".format(rid))
                    resource.fix_irods_user_paths(echo_actions=not options['log'],
                                                  log_actions=options['log'],
                                                  return_actions=False)
                else:
                    print("Resource with id {} is not a default userspace resource".format(rid))


        else:  # fix all userspace resources
            print("REMAPPING ALL USERSPACE RESOURCES TO LOCAL USERSPACE")
            # only for resources with default federation paths in userspace
            for r in BaseResource.objects.filter(resource_federation_path=defaultpath):
                r.fix_irods_user_paths(echo_actions=not options['log'],  # Don't both log and echo
                                       log_actions=options['log'],
                                       return_actions=False)
