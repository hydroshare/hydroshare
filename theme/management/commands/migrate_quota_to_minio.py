import subprocess
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from theme.models import UserQuota


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
        for quota in UserQuota.objects.all():
            try:
                subprocess.run(["mc", "quota", "set", f"{quota.zone}/{quota.user.userprofile.bucket_name}",
                                "--size", f"{quota.allocated_value}{_convert_unit(quota.unit)}"],
                               check=True,
                               )
            except subprocess.CalledProcessError as e:
                print(f"Quota for {quota.user.username} in {quota.zone} not set")
