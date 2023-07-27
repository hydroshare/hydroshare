# -*- coding: utf-8 -*-

"""
Fix resource file duplicates

This checks that there is only one ResourceFile for each iRods file

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from hs_core.models import ResourceFile, BaseResource

import logging


class Command(BaseCommand):
    help = "Fix ResourceFile duplicates."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dryrun',
            action='store_true',
            dest='dryrun',
            default=False,
            help='Find duplicates but dont fix them',
        )

    def handle(self, *args, **options):
        logger = logging.getLogger(__name__)
        dry_run = options['dryrun']

        print("REPAIRING ALL RESOURCES")
        dup_resource_files = ResourceFile.objects.values('resource_file', 'object_id').annotate(count=Count('id')).values('resource_file', 'object_id').order_by().filter(count__gt=1)
        if dup_resource_files:
            total = dup_resource_files.count()
            current = 1
            print(f"Discovered the following duplicate file objects:\n {dup_resource_files}")
            for resourcefile in dup_resource_files:
                filename=resourcefile["resource_file"]
                print(f"{current}/{total} Repairing file {filename}")
                if not dry_run:
                    resourcefiles_to_remove = ResourceFile.objects.filter(resource_file=filename)
                    ResourceFile.objects.filter(pk__in=resourcefiles_to_remove.values_list('pk')[1:]).delete()
                else:
                    print(f"Repair of {filename} skipped due to dryrun")
                current += 1
