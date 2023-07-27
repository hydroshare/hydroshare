# -*- coding: utf-8 -*-

"""
Fix resource file duplicates

This checks that there is only one ResourceFile for each iRods file

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from hs_core.models import ResourceFile


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
        dry_run = options['dryrun']

        dup_resource_files = ResourceFile.objects.values('resource_file', 'object_id') \
            .annotate(count=Count('id')) \
            .values('resource_file', 'object_id') \
            .order_by() \
            .filter(count__gt=1)
        if dup_resource_files:
            total = dup_resource_files.count()
            current = 1
            print(f"Discovered the following duplicate file objects:\n {dup_resource_files}")
            for resourcefile in dup_resource_files:
                filename = resourcefile["resource_file"]
                if not dry_run:
                    print(f"{current}/{total} Repairing file {filename}")
                    resourcefiles_to_remove = ResourceFile.objects.filter(resource_file=filename)
                    ResourceFile.objects.filter(pk__in=resourcefiles_to_remove.values_list('pk')[1:]).delete()
                else:
                    print(f"{current}/{total} Repair of {filename} skipped due to dryrun")
                current += 1
