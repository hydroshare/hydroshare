# -*- coding: utf-8 -*-

"""
Fix resource file duplicates

This checks that there is only one ResourceFile for each iRods file

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Count

from hs_composite_resource.models import CompositeResource
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

        # first we remove files with content_type other than the content type for CompositeResource
        desired_content_type = ContentType.objects.get_for_model(CompositeResource)
        non_conforming_files = ResourceFile.objects.exclude(content_type=desired_content_type).only('id')
        print(f"Non-conforming files to be removed:\n{non_conforming_files}")
        if dry_run:
            print("Skipping file delete due to dryrun")
        else:
            non_conforming_files.delete()

        dup_resource_files = ResourceFile.objects.values('resource_file', 'object_id') \
            .annotate(count=Count('id')) \
            .order_by() \
            .filter(count__gt=1)
        if dup_resource_files:
            total_resfile_containing_dups = dup_resource_files.count()
            current_resfile = 1
            print(f"Discovered the following duplicate file objects:\n {dup_resource_files}")
            for resourcefile in dup_resource_files:
                filename = resourcefile["resource_file"]
                num_duplicate_paths = resourcefile['count']
                if not dry_run:
                    print(f"{current_resfile}/{total_resfile_containing_dups} \
                          Repairing file {filename} by removing {num_duplicate_paths -1} paths.")
                    resourcefiles_to_remove = ResourceFile.objects \
                        .filter(resource_file=filename, object_id=resourcefile['object_id'])
                    ResourceFile.objects.filter(pk__in=resourcefiles_to_remove.values_list('pk')[1:]).delete()
                else:
                    print(f"{current_resfile}/{total_resfile_containing_dups} \
                          Repair of {filename} skipped due to dryrun. Would remove {num_duplicate_paths -1} paths.")
                current_resfile += 1
