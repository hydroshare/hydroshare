from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from theme.models import UserQuota
from hs_core.tasks import update_quota_usage_task

class Command(BaseCommand):
    help = "Update used storage space in UserQuota table for all users in HydroShare by reading " \
           "quota usage AVUs for users which are updated by iRODS quota update micro-services." \
           "This management command needs to be run initially to update Django DB quota usage " \
           "or whenever iRODS quota update micro-services are reset and Django DB needs to be " \
           "brought in sync with iRODS quota AVUs"

    def handle(self, *args, **options):
        for u in User.objects.all():
            if UserQuota.objects.filter(user=u).exists() and u.is_active and not u.is_superuser:
                update_quota_usage_task(u.username)
