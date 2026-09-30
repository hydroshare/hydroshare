"""List <bucket_name>/<resource_short_id> pairs for recently updated resources.

Intended to be piped into scripts/mirror-prod-minio-users-to-gcs.sh so that only
resources with recent changes get mirrored to GCS, e.g.:

    python manage.py list_recently_updated_resource_buckets --hours 24 \
        | PROD_ALIAS=prod-minio GCS_ALIAS=gcs GCS_BUCKET=hydroshare-resources \
          ./scripts/mirror-prod-minio-users-to-gcs.sh
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from hs_core.models import BaseResource


class Command(BaseCommand):
    help = (
        "Print '<bucket_name>/<resource_short_id>' (one per line) for every resource "
        "updated within the last N hours (default 24). The bucket_name is the S3 "
        "bucket of the resource's quota holder."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=float,
            default=24,
            help='Look back this many hours for resource updates (default: 24).',
        )

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(hours=options['hours'])
        # last_updated is a derived property (not a DB column), so it can't be filtered
        # or ordered at the query level; evaluate it per resource instead.
        resources = (
            BaseResource.objects
            .select_related('quota_holder__userprofile')
            .iterator()
        )
        resources = sorted(
            (r for r in resources if r.last_updated and r.last_updated >= since),
            key=lambda r: r.last_updated,
        )

        for resource in resources:
            quota_holder = resource.quota_holder
            if quota_holder is None:
                self.stderr.write(
                    f"Skipping resource {resource.short_id}: no quota_holder set."
                )
                continue

            bucket_name = getattr(quota_holder.userprofile, 'bucket_name', None)
            if not bucket_name:
                self.stderr.write(
                    f"Skipping resource {resource.short_id}: quota holder "
                    f"'{quota_holder.username}' has no bucket_name."
                )
                continue

            if bucket_name == "published":
                self.stdout.write(f"mc mirror --overwrite --remove hydroshare/{bucket_name}/{resource.short_id} \
                    gcs/hydroshare-403701-prod-cloud-native-published/{resource.short_id}")
            elif bucket_name == "ciroh-data":
                self.stdout.write(f"mc mirror --overwrite --remove hydroshare/{bucket_name}/{resource.short_id} \
                    gcs/hydroshare-403701-prod-cloud-native-ciroh/{resource.short_id}")
            else:
                self.stdout.write(f"mc mirror --overwrite --remove hydroshare/{bucket_name}/{resource.short_id} \
                    gcs/hydroshare-403701-prod-cloud-native-resource/{resource.short_id}")
