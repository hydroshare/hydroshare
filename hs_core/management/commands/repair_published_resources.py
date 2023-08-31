# -*- coding: utf-8 -*-

"""
Check synchronization between iRODS and Django for published resources

This checks that:

1. every ResourceFile corresponds to an iRODS file
2. every iRODS file in {short_id}/data/contents corresponds to a ResourceFile
3. every iRODS directory {short_id} corresponds to a Django resource

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import repair_resource
from hs_core import hydroshare

import logging


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--dryrun',
            action='store_true',  # True for presence, False for absence
            dest='dry_run',  # value is options['dry_run']
            help='run process without saving changes',
        )

    def handle(self, *args, **options):

        logger = logging.getLogger(__name__)
        dry_run = options['dry_run']
        site_url = hydroshare.utils.current_site_url()

        resources = BaseResource.objects.filter(raccess__published=True)
        total_published = resources.count()
        impacted_resources = 0
        total_files_missing_in_django = 0
        total_files_dangling_in_django = 0
        resources_with_missing_django = []
        resources_with_missing_irods = []
        for count, resource in enumerate(resources):
            res_url = site_url + resource.get_absolute_url()
            print("*" * 100)
            print(f"{count}/{total_published}: Checking resource {res_url}")
            ingest, missing_in_django, dangling_in_django = repair_resource(resource, logger, dry_run=dry_run)
            if dangling_in_django > 0 or missing_in_django > 0:
                impacted_resources += 1
                total_files_missing_in_django += missing_in_django
                total_files_dangling_in_django += dangling_in_django
                if missing_in_django > 0:
                    resources_with_missing_django.append(res_url)
                if dangling_in_django > 0:
                    resources_with_missing_irods.append(res_url)
                print(f"{ingest} files ingested into Django for this resource.")
                print(f"{dangling_in_django} files missing in iRods for this resource.")
                print(f"{missing_in_django} files missing in Django for this resource.")
                print(f"Resources thus far with at least one missing django file: {len(resources_with_missing_django)}")
                print(f"Resources thus far with at least one missing irods file: {len(resources_with_missing_irods)}")
                print(f"Total resources with discrepancies thus far: {impacted_resources}")
        print("*" * 100)
        print("*" * 100)
        print(f"Number of resources that had at least one file issue: {impacted_resources}")

        print("*" * 100)
        print(f"Total number of files missing in Django (across all resources): {total_files_missing_in_django}")
        print(f"Number of resources with at least one missing django file: {len(resources_with_missing_django)}")
        for res in resources_with_missing_django:
            print(res)

        print("*" * 100)
        print(f"Total number of files missing in iRods (across all resources): {total_files_dangling_in_django}")
        print(f"Number of resources with at least one missing irods file: {len(resources_with_missing_irods)}")
        for res in resources_with_missing_irods:
            print(res)
