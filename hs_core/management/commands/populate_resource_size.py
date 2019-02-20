# -*- coding: utf-8 -*-

"""
Calculates the size of a resource and saves it to the size field for quick reference
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Recalculate the size of specified resources"

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
        resource_counter_success = 0
        resource_counter = 0
        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.
            for rid in options['resource_ids']:
                print("> Calculating resource size for {}".format(rid))
                try:
                    resource = BaseResource.objects.get(short_id=rid)
                    resource_counter += 1
                    resource.calculate_size
                    resource_counter_success += 1
                except Exception as e:
                    print("Error processing {}".format(resource.short_id))
                    print(e)
                    print(e.message)
                    continue

        else:  # check all composite resources and create bag files
            print("> Calculating resource size for all resources")
            for resource in BaseResource.objects.all():
                print("> Calculating resource size for {}".format(resource.short_id))
                resource_counter += 1
                try:
                    resource.calculate_size
                    resource_counter_success += 1
                except Exception as e:
                    print("Error processing {}".format(resource.short_id))
                    print(e)
                    print(e.message)
                    continue
        print("Calculated Resource size for {} resources".format(resource_counter))
