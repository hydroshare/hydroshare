# -*- coding: utf-8 -*-

"""
Register web services for resource(s)
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_core.tasks import check_geoserver_registrations
from django.utils import timezone
from datetime import timedelta
from django.http.response import Http404


class Command(BaseCommand):
    help = "Register web services for resource(s)"

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)
        parser.add_argument('--days', type=int, dest='days', help='include resources updated in the last X days')
        parser.add_argument('--async',
                            action='store_true',  # True for presence, False for absence
                            dest='run_async',
                            help='web services requests should run async through celery')

    def handle(self, *args, **options):
        resources = options['resource_ids']
        days = options['days']
        run_async = options['run_async']

        if resources and days:
            print("Please only include either [resources] or [days] argument, but not both")
            return

        if resources:  # an array of resource short_id to check.
            print("CHECKING RESOURCES PROVIDED")
            found_resources = []
            for rid in resources:
                try:
                    resource = get_resource_by_shortkey(rid)
                    found_resources.append(resource)
                except (BaseResource.DoesNotExist, Http404):
                    msg = f"resource {rid} not found"
                    print(msg)
                    continue
            resources = found_resources

        elif days:
            print(f"CHECKING ALL PUBLIC RESOURCES UPDATED IN LAST {days} DAYS")
            cuttoff_time = timezone.now() - timedelta(days)
            resources = BaseResource.objects.filter(updated__gte=cuttoff_time, raccess__public=True)

        else:
            print("CHECKING ALL PUBLIC RESOURCES")
            resources = BaseResource.objects.filter(raccess__public=True)
        if resources:
            if run_async:
                check_geoserver_registrations(resources, run_async=True)
                print("WEB SERVICE CHECKS WILL RUN ASYNC. CHECK CELERY FOR STATUS.")
            else:
                check_geoserver_registrations(resources, run_async=False)
                print("DONE UPDATING WEB SERVICES")
        else:
            print("No resources found matching provided args.")
