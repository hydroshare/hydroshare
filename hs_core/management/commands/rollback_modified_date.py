"""
Rollback incorrectly-bumped modified timestamps on collection-related resources.

Can be run in two modes:

  1. CSV mode — reads a CSV with columns 'short_id' and 'new_modified_timestamp' (ISO 8601 format)
       and corrects all listed resources:
       python manage.py rollback_modified_date --csv /path/to/collection_resources_diff.csv

  2. Single-resource mode — correct one resource directly:
       python manage.py rollback_modified_date --resource <short_id> --modified <ISO timestamp>
       e.g. python manage.py rollback_modified_date --resource abc123 --modified 2025-11-01T12:00:00+00:00

Optional flags:
  --dry-run   Report what would be changed without writing anything
  --debug     Stop on any exception instead of continuing
"""

import csv
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from hs_core.models import BaseResource, Date


class Command(BaseCommand):
    help = "Rollback incorrectly-bumped modified timestamps on resources"

    def add_arguments(self, parser):
        mode = parser.add_mutually_exclusive_group(required=True)
        mode.add_argument(
            "--csv",
            dest="csv_path",
            help="Path to a corrections CSV (must have 'short_id' and 'new_modified_timestamp' columns)",
        )
        mode.add_argument(
            "--resource",
            dest="resource_id",
            help="Short ID of a single resource to correct",
        )

        parser.add_argument(
            "--modified",
            dest="modified",
            help="ISO 8601 timestamp to restore (required with --resource)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Report what would be changed without writing anything",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            dest="debug",
            help="Stop on any exception instead of continuing",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        debug = options["debug"]

        if dry_run:
            self.stdout.write("DRY RUN — no changes will be written.\n")

        if options["resource_id"]:
            if not options["modified"]:
                raise Exception("--modified <ISO timestamp> is required when using --resource")
            rows = {options["resource_id"]: options["modified"]}
        else:
            rows = self._load_csv(options["csv_path"])
            self.stdout.write(f"Loaded {len(rows)} resources from {options['csv_path']}\n")

        updated = 0
        skipped = 0
        errored = 0

        for short_id, updated_modified in rows.items():
            try:
                self._rollback_resource(short_id, updated_modified, dry_run)
                updated += 1
                self.stdout.write(f"  {'[DRY RUN] ' if dry_run else ''}updated {short_id} -> {updated_modified}")
            except BaseResource.DoesNotExist:
                self.stdout.write(f"  SKIP {short_id}: not found in Django")
                skipped += 1
            except Exception as e:
                self.stdout.write(f"  ERROR {short_id}: {e}")
                errored += 1
                if debug:
                    raise

            if not dry_run:
                try:
                    resource = BaseResource.objects.get(short_id=short_id)
                    resource.write_django_metadata_json_files()
                except BaseResource.DoesNotExist:
                    pass
                except Exception as e:
                    self.stdout.write(f"  WARNING {short_id}: write_django_metadata_json_files failed: {e}")
                    if debug:
                        raise

        self.stdout.write(
            f"\nDone. updated={updated}, skipped={skipped}, errors={errored}"
        )

    def _load_csv(self, path):
        """Return dict of short_id -> new_modified_timestamp (non-empty rows only)."""
        rows = {}
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                new_modified = row.get("new_modified_timestamp", "").strip()
                if new_modified:
                    rows[row["short_id"]] = new_modified
        return rows

    @transaction.atomic
    def _rollback_resource(self, short_id, updated_modified_str, dry_run):
        resource = BaseResource.objects.get(short_id=short_id)
        metadata = resource.metadata

        # Parse the modified timestamp to update to from ISO 8601 string to a datetime object
        modified_dt = datetime.fromisoformat(updated_modified_str)

        if not dry_run:
            # 1. Update the Date metadata element
            Date.objects.filter(
                object_id=metadata.id,
                content_type=ContentType.objects.get_for_model(metadata),
                type="modified",
            ).update(start_date=modified_dt)

            # 2. Update cached_metadata JSON field
            cached = dict(resource.cached_metadata)
            cached["modified"] = updated_modified_str
            BaseResource.objects.filter(short_id=short_id).update(cached_metadata=cached)
