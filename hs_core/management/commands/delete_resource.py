# -*- coding: utf-8 -*-

"""
Delete a partially deleted resource from Django

"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.resource import delete_resource


class Command(BaseCommand):
    help = "Delete a resource from django."

    def add_arguments(self, parser):

        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    BaseResource.objects.get(short_id=rid)
                    delete_resource(rid)
                    print("Resource with id {} DELETED from Django".format(rid))
                except BaseResource.DoesNotExist:
                    print("Resource with id {} NOT FOUND in Django".format(rid))
