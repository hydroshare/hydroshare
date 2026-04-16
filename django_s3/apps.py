import subprocess
from django.apps import AppConfig
from .settings import get_resource_s3_zones_config


class DjangoS3AppConfig(AppConfig):
    name = "django_s3"

    def ready(self):
        from .storage import S3Storage
        istorage = S3Storage()
        settings_config = get_resource_s3_zones_config()
        for zone_name, zone_config in settings_config.resource_s3_zones_config.items():
            bucket_name = zone_config.bucket_name
            try:
                istorage.connection(zone_name).meta.client.head_bucket(Bucket=bucket_name)
            except Exception:
                istorage.connection(zone_name).create_bucket(Bucket=bucket_name)
                subprocess.run(["mc", "event", "add", f"{zone_name}/{bucket_name}",
                            "arn:minio:sqs::RESOURCEFILE:kafka", "--event", "put,delete"], check=True)
