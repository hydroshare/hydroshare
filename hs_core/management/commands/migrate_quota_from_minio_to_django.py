"""
This command Migrates the quota from MinIO to UserQuota fields.
"""
from django.core.management.base import BaseCommand
from theme.models import UserQuota
from hs_core.models import BaseResource
import subprocess


def allocated_value_size_and_unit(user_quota):
    try:
        result = subprocess.run(
            ["mc", "quota", "info", f"hydroshare/{user_quota.user.userprofile.bucket_name}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        result_split = result.stdout.split(" ")
        unit = result_split[-1].strip()
        unit = unit.replace("i", "")
        size = result_split[-2]
        return (float(size), unit)
    except (subprocess.CalledProcessError, ValueError, IndexError) as e:
        print(f"Error occurred for user quota {user_quota.user.username}: {e}")
        return (20, "GB")


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
            user_quotas = UserQuota.objects.filter(
                user__is_active=True,
                user__pk__in=BaseResource.objects.values_list('quota_holder_id', flat=True),
            )
        count = 0
        quota_updated = 0
        for user_quota in user_quotas:
            size, unit = allocated_value_size_and_unit(user_quota)
            if size != 20.0 or unit != "GB":
                if size > 0:
                    print(f"Setting quota for {user_quota.user.username} to {size} {unit}")
                    user_quota.allocated_value = size
                    user_quota.unit = unit
                    user_quota.save()
                    quota_updated += 1
            if user_quota.allocated_value == 0:
                print(f"Resetting user quota to default for {user_quota.user.username}")
                user_quota.allocated_value = 20
                user_quota.unit = "GB"
                user_quota.save()
                quota_updated += 1
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} user quotas so far, updated {quota_updated} quotas.")
        print(f"Processed {count} user quotas, updated {quota_updated} quotas.")
