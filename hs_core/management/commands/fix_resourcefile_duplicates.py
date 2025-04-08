# -*- coding: utf-8 -*-

"""
Fix resource file duplicates

This checks that there is only one ResourceFile for each S3 file

* By default, prints errors on stdout.
* Optional argument --log instead logs output to system log.
"""

import logging
from django.core.management.base import BaseCommand
from hs_core.management.utils import fix_resourcefile_duplicates


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
        logger = logging.getLogger(__name__)
        fix_resourcefile_duplicates(dry_run=dry_run, logger=logger)
