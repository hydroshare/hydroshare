import subprocess
from django.core.management.base import BaseCommand

from theme.models import UserQuota
from hs_core.models import BaseResource
from django_s3.storage import S3Storage


def _convert_unit(unit):
    if len(unit) == 2:
        return f'{unit[0]}i{unit[1]}'
    return unit


class Command(BaseCommand):
    """
    Migrate quota to minio
    """
    help = "Migrate quota to minio"

    def handle(self, *args, **options):
        istorage = S3Storage()
        for quota in UserQuota.objects.all():
            if istorage.bucket_exists(quota.user.user_profile.bucket_name):
                resources = BaseResource.objects.filter(quota_holder_id=quota.user.id)
                if resources.exists():
                    try:
                        subprocess.run(["mc", "quota", "set", f"{quota.zone}/{quota.user.userprofile.bucket_name}",
                                        "--size", f"{quota.allocated_value}{_convert_unit(quota.unit)}"],
                                       check=True,
                                       )
                    except subprocess.CalledProcessError:
                        print(f"Quota for {quota.user.username} in {quota.zone} not set")
