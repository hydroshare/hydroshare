from urllib.parse import urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from pydantic import ValidationError

from django_s3.models import StorageZone
from django_s3.settings import ZoneConfig


class Command(BaseCommand):
    help = "Replace active storage zones with the configured local MinIO zones."

    def add_arguments(self, parser):
        parser.add_argument("--confirm", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Pass --confirm to disable imported zones and configure local MinIO.")
        if not getattr(settings, "S3_ZONES_DATABASE_ENABLED", False):
            raise CommandError("S3_ZONES_DATABASE_ENABLED must be true.")
        if settings.RESOURCE_S3_DEFAULT_ZONE != "hydroshare":
            raise CommandError("Local MinIO initialization requires hydroshare as the default zone.")

        configs = getattr(settings, "RESOURCE_S3_ZONES_CONFIG", {})
        if not isinstance(configs, dict) or settings.RESOURCE_S3_DEFAULT_ZONE not in configs:
            raise CommandError("Local zone configuration must include the default zone.")

        zones = {}
        names = set()
        for name, config in configs.items():
            try:
                zone_config = ZoneConfig(**config)
            except (TypeError, ValidationError) as exc:
                raise CommandError(f"Invalid local zone configuration for {name!r}.") from exc
            if zone_config.aws_s3_endpoint_url.rstrip("/") != "http://minio:9000":
                raise CommandError(f"Zone {name!r} must use the local MinIO endpoint http://minio:9000.")
            public_endpoint = urlsplit(zone_config.aws_s3_endpoint_url_public)
            if (public_endpoint.scheme != "http"
                    or public_endpoint.hostname not in ("localhost", "127.0.0.1", "::1", "host.docker.internal")):
                raise CommandError(f"Zone {name!r} must use a local HTTP public endpoint.")
            if not zone_config.aws_access_key_id or not zone_config.aws_secret_access_key:
                raise CommandError(f"Zone {name!r} must have local MinIO credentials.")
            for bucket_name in (zone_config.bucket_name, zone_config.alias):
                if bucket_name and bucket_name in names:
                    raise CommandError(f"Duplicate bucket or alias {bucket_name!r}.")
                if bucket_name:
                    names.add(bucket_name)
            zones[name] = zone_config

        StorageZone.objects.update(enabled=False)
        for name, config in zones.items():
            zone, _ = StorageZone.objects.get_or_create(
                name=name,
                defaults={
                    "bucket_name": config.bucket_name,
                    "endpoint": config.aws_s3_endpoint_url,
                    "public_endpoint": config.aws_s3_endpoint_url_public,
                    "access_key": config.aws_access_key_id,
                    "encrypted_secret": b"",
                    "enabled": False,
                },
            )
            zone.bucket_name = config.bucket_name
            zone.alias = config.alias
            zone.endpoint = config.aws_s3_endpoint_url
            zone.public_endpoint = config.aws_s3_endpoint_url_public
            zone.access_key = config.aws_access_key_id
            zone.region = config.region
            zone.copy_method = config.copy_method
            zone.multipart_copy_threshold = config.multipart_copy_threshold
            zone.enabled = True
            zone.set_secret(config.aws_secret_access_key)
            zone.full_clean()
            zone.save()
        self.stdout.write(self.style.SUCCESS("Local MinIO zones configured. Restart all zone consumers."))
