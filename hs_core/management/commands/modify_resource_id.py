# -*- coding: utf-8 -*-

"""
Modify the resource id of an existing resource

"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Modify the resource id of an existing resource"

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_id', nargs='*', type=str)
        parser.add_argument('new_resource_id', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['new_resource_id']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    BaseResource.objects.get(short_id=rid)
                    delete_resource(rid)
                    print("Resource with id {} DELETED from Django".format(rid))
                except BaseResource.DoesNotExist:
                    print("Resource with id {} NOT FOUND in Django".format(rid))
