"""
This command Migrates the quota from MinIO to UserQuota fields.
"""
from django.core.management.base import BaseCommand
from theme.models import UserQuota
from django.conf import settings
import subprocess


def allocated_value_size_and_unit(user_quota):
    try:
        result = subprocess.run(
            ["mc", "quota", "info", f"{user_quota.zone}/{user_quota.user.userprofile.bucket_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return settings.DEFAULT_QUOTA_VALUE, settings.DEFAULT_QUOTA_UNIT
    result_split = result.stdout.split(" ")
    unit = result_split[-1].strip()
    unit = unit.replace("i", "")
    size = result_split[-2]
    return float(size), unit


class Command(BaseCommand):
    help = "Assign bucket names to users missing them"

    def add_arguments(self, parser):
        # a list of usernames, or none to check all users
        parser.add_argument('usernames', nargs='*', type=str)

    def handle(self, *args, **options):
        usernames = options.get('usernames', [])
        if usernames:
            user_quotas = UserQuota.objects.filter(user__username__in=usernames)
        else:
            user_quotas = UserQuota.objects.filter(user__is_active=True)
        for user_quota in user_quotas:
            size, unit = allocated_value_size_and_unit(user_quota)
            print(f"Settings quota for {user_quota.user.username} to {size} {unit}")
            user_quota.allocated_value = size
            user_quota.unit = unit
            user_quota.save()
