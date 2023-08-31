# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django for multiple resources

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile
3. every iRODS directory {short_id} corresponds to a Django resource
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import repair_resource
from hs_core import hydroshare
from django.utils import timezone
from datetime import timedelta

import logging


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)
        parser.add_argument('--days', type=int, dest='days', help='include resources updated in the last X days')
        # Named (optional) arguments
        parser.add_argument(
            '--dryrun',
            action='store_true',  # True for presence, False for absence
            dest='dry_run',  # value is options['dry_run']
            help='run process without saving changes',
        )
        parser.add_argument(
            '--published',
            action='store_true',  # True for presence, False for absence
            dest='published',  # value is options['dry_run']
            help='filter to just published resources',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resources_ids = options['resource_ids']
        resources = BaseResource.objects.all()
        days = options['days']
        dry_run = options['dry_run']
        published = options['published']
        site_url = hydroshare.utils.current_site_url()

        if resources_ids:  # an array of resource short_id to check.
            print("CHECKING RESOURCES PROVIDED")
            resources = resources.filter(short_id__in=resources_ids)
        if published:
            if not dry_run:
                print("Executing with --published arg implies --dryrun. No modifications will be saved.")
                dry_run = True
            if resources_ids:
                print("Can't supply resource_ids in addition to --published arg. Choose one or the other.")
                return
            print("FILTERING TO INCLUDE PUBLISHED RESOURCES ONLY")
            resources = resources.filter(raccess__published=True)

        if days:
            print(f"FILTERING TO INCLUDE RESOURCES UPDATED IN LAST {days} DAYS")
            cuttoff_time = timezone.now() - timedelta(days)
            resources = resources.filter(updated__gte=cuttoff_time)

        if not resources:
            print("NO RESOURCES FOUND MATCHING YOUR FILTER ARGUMENTS")
            return

        total_res_to_check = resources.count()
        impacted_resources = 0
        total_files_missing_in_django = 0
        total_files_dangling_in_django = 0
        resources_with_missing_django = []
        resources_with_missing_irods = []
        for count, resource in enumerate(resources):
            res_url = site_url + resource.get_absolute_url()
            print("*" * 100)
            print(f"{count}/{total_res_to_check}: Checking resource {res_url}")
            missing_in_django, dangling_in_django = repair_resource(resource, logger, dry_run=dry_run)
            if dangling_in_django > 0 or missing_in_django > 0:
                impacted_resources += 1
                total_files_missing_in_django += missing_in_django
                total_files_dangling_in_django += dangling_in_django
                if missing_in_django > 0:
                    resources_with_missing_django.append(res_url)
                if dangling_in_django > 0:
                    resources_with_missing_irods.append(res_url)
                print(f"{dangling_in_django} files dangling in Django for this resource.")
                print(f"{missing_in_django} files missing in Django for this resource.")
                print(f"Resources thus far with at least one missing django file: {len(resources_with_missing_django)}")
                print(f"Resources thus far with at least one dangling django file: {len(resources_with_missing_irods)}")
                print(f"Total resources with discrepancies thus far: {impacted_resources}")
        print("*" * 100)
        print("*" * 100)
        print(f"Number of resources that had at least one file issue: {impacted_resources}")

        print("*" * 100)
        print(f"Total number of files missing in Django (across all checked resources): \
              {total_files_missing_in_django}")
        print(f"Number of resources with at least one missing django file: {len(resources_with_missing_django)}")
        for res in resources_with_missing_django:
            print(res)

        print("*" * 100)
        print(f"Total number of files dangling in Django (across all checked resources): \
              {total_files_dangling_in_django}")
        print(f"Number of resources with at least one missing irods file: {len(resources_with_missing_irods)}")
        for res in resources_with_missing_irods:
            print(res)
