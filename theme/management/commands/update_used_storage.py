from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from theme.models import UserQuota
from hs_core.tasks import update_quota_usage
from hs_core.hydroshare import current_site_url


class Command(BaseCommand):
    help = "Update used storage space in UserQuota table for all users in HydroShare by reading " \
           "quota usage AVUs for users which are updated by iRODS quota update micro-services." \
           "This management command needs to be run initially to update Django DB quota usage " \
           "or whenever iRODS quota update micro-services are reset and Django DB needs to be " \
           "brought in sync with iRODS quota AVUs"

    def handle(self, *args, **options):
        errors = {}
        users = User.objects.filter(is_active=True, is_superuser=False)
        count = users.count()
        for i, u in enumerate(users, start=0):
            i += 1
            if UserQuota.objects.filter(user=u).exists():
                count_string = f"{i}/{count}:"
                profile = f"{current_site_url()}/user/{u.id}"
                try:
                    update_quota_usage(u.username)
                    print(f"{count_string}Success updating quota in Django for {u.username}: {profile}")
                except ValidationError as e:
                    print(f"{count_string}{profile} Error updating quota:{e.message}")
                    errors[profile] = e.message
        print("Completed updating quotas.")
        if errors:
            for profile, message in errors:
                print(f"Error encountered while updating quota for {profile}: {message}")
