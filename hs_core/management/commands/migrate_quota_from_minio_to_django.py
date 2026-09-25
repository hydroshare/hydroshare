"""
This command Migrates the quota from MinIO to UserQuota fields.
"""
from django.core.management.base import BaseCommand
from theme.models import UserQuota
from hs_core.models import BaseResource
import subprocess


class BucketNotFoundError(Exception):
    pass


def allocated_value_size_and_unit(user_quota):
    if not BaseResource.objects.filter(quota_holder=user_quota.user).exists():
        print(f"No resources for user quota: {user_quota.user.username}")
        return (20, "GB")
    try:
        result = subprocess.run(
            ["mc", "quota", "info", f"{user_quota.zone}/{user_quota.user.userprofile.bucket_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        if "specified bucket does not exist" in e.stderr:
            print(f"Bucket does not exist for user quota: {user_quota.user.username}")
            return (20, "GB")
    except (ValueError, IndexError):
        raise RuntimeError(f"Failed to get allocated value for user quota: {user_quota.user.username}")
    result_split = result.stdout.split(" ")
    unit = result_split[-1].strip()
    unit = unit.replace("i", "")
    size = result_split[-2]
    return (float(size), unit) if float(size) > 0 else (20, "GB")


class Command(BaseCommand):
    help = "Migrates the quota from MinIO to UserQuota fields."

    def add_arguments(self, parser):
        # a list of usernames, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        usernames = options.get('usernames', [])
        if usernames:
            user_quotas = UserQuota.objects.filter(user__username__in=usernames)
        else:
            user_quotas = UserQuota.objects.filter()
        for user_quota in user_quotas:
            try:
                size, unit = allocated_value_size_and_unit(user_quota)
            except BucketNotFoundError as e:
                self.stderr.write(self.style.WARNING(str(e)))
                continue
            if size == 20.0 and unit == "GB":
                print(f"Default quota skipping {user_quota.user.username}")
            else:
                print(f"Setting quota for {user_quota.user.username} to {size} {unit}")
                user_quota.allocated_value = size
                user_quota.unit = unit
                user_quota.save()
