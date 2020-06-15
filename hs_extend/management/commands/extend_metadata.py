# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey


class Command(BaseCommand):
    help = "Computed extended metadata for discovery"

    def add_arguments(self, parser):
        # a list of resource id's, or none to check all resources
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                try:
                    resource = get_resource_by_shortkey(rid)
                except BaseResource.NotFoundException:
                    msg = "resource {} not found".format(rid)
                    print(msg)
                    continue
                print("Indexing resource {}".format(rid))

        else:  # check all resources
            print("Indexing all resources")
            for r in BaseResource.objects.all():
                try:
                    resource = get_resource_by_shortkey(r.short_id)
                except BaseResource.NotFoundException:
                    msg = "resource {} not found".format(r.short_id)
                    print(msg)
                    continue
                print("Indexing resource {}".format(r.short_id))
