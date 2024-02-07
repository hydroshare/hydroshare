# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django for multiple resources

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile
3. every iRODS directory {short_id} corresponds to a Django resource
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError
from hs_core.models import BaseResource
from hs_core.management.utils import repair_resource
from hs_core.views.utils import get_default_admin_user
from hs_core import hydroshare
from django.utils import timezone
from django.db.models import F
from datetime import timedelta

import logging


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        parser.add_argument('resource_ids', nargs='*', type=str)
        parser.add_argument('--updated_since', type=int, dest='updated_since',
                            help='include only resources updated in the last X days')
        parser.add_argument('--ingored_repaired_since', type=int, dest='ingored_repaired_since',
                            help='ignore resources repaired since X days ago')
        parser.add_argument(
            '--admin',
            action='store_true',  # True for presence, False for absence
            dest='admin',  # value is options['dry_run']
            help='run process as admin user - this allows published resources to be modified',
        )
        parser.add_argument(
            '--dryrun',
            action='store_true',  # True for presence, False for absence
            dest='dry_run',  # value is options['dry_run']
            help='run process without saving changes',
        )
        parser.add_argument(
            '--published',
            action='store_true',  # True for presence, False for absence
            dest='published',  # value is options['published']
            help='filter to just published resources',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        resources_ids = options['resource_ids']
        resources = BaseResource.objects.all()
        updated_since = options['updated_since']
        admin = options['admin']
        dry_run = options['dry_run']
        published = options['published']
        site_url = hydroshare.utils.current_site_url()
        ingored_repaired_since = options['ingored_repaired_since']

        if resources_ids:  # an array of resource short_id to check.
            print("CHECKING RESOURCES PROVIDED")
            resources = resources.filter(short_id__in=resources_ids)
        if published:
            if not dry_run:
                print("WARNING: Executing with --published arg without --dryrun. Published resources will be modified.")
            print("FILTERING TO INCLUDE PUBLISHED RESOURCES ONLY")
            resources = resources.filter(raccess__published=True)

        if updated_since:
            print(f"FILTERING TO INCLUDE RESOURCES UPDATED IN LAST {updated_since} DAYS")
            if resources_ids:
                print("Your supplied resource_ids will be filtered by the --updated_since days that you provided. ")
            cuttoff_time = timezone.now() - timedelta(updated_since)
            resources = resources.filter(updated__gte=cuttoff_time)

        if ingored_repaired_since:
            print(f"FILTERING TO INCLUDE RESOURCES NOT REPAIRED IN THE LAST {ingored_repaired_since} DAYS")
            cuttoff_time = timezone.now() - timedelta(days=ingored_repaired_since)
            resources = resources.filter(repaired__lt=cuttoff_time)

        if dry_run:
            print("CONDUCTING A DRY RUN: FIXES WILL NOT BE SAVED")

        if not resources:
            print("NO RESOURCES FOUND MATCHING YOUR FILTER ARGUMENTS")
            return

        if admin:
            print("PROCESSES WILL BE RUN AS ADMIN USER. ALLOWS DELETING DJANGO RESOURCE FILES ON PUBLISHED RESOURCES")
            user = get_default_admin_user()
        else:
            user = None

        resources = resources.order_by(F('repaired').asc(nulls_first=True))

        total_res_to_check = resources.count()
        current_resource = 0
        impacted_resources = 0
        total_files_missing_in_django = 0
        total_files_dangling_in_django = 0
        resources_with_missing_django = []
        resources_with_missing_irods = []
        failed_resources = []
        for resource in resources.iterator():
            current_resource += 1
            res_url = site_url + resource.absolute_url
            print("*" * 100)
            print(f"{current_resource}/{total_res_to_check}: Checking resource {res_url}")
            if resource.raccess.published:
                print("This Resource is published")
                if admin:
                    print("Command running with --admin. Published resources will be repaired if needed.")
                else:
                    print("Command running without --admin. Fixing a published resource raise ValidationError")
            try:
                _, missing_in_django, dangling_in_django = repair_resource(resource, logger, dry_run=dry_run, user=user)
            except ValidationError as ve:
                failed_resources.append(res_url)
                print("Exception while attempting to repair resource:")
                print(ve)
                continue
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
        print(f"Number of resources with at least one dangling Django file: {len(resources_with_missing_irods)}")
        for res in resources_with_missing_irods:
            print(res)

        # Make it simple to detect clean/fail run in Jenkins
        if impacted_resources and dry_run:
            raise CommandError("repair_resources detected resources in need of repair during dry run")
        else:
            print("Completed run of repair_resource")
        if failed_resources:
            print("*" * 100)
            print("Repair was attempted but failed for the following resources:")
            for res in resources_with_missing_irods:
                print(res)
            raise CommandError("Repair was attempted but failed on at least one resource")
