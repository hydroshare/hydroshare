from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from theme.models import UserQuota


class Command(BaseCommand):
    help = "This command can be run to fix the corrupt user data where some users do not " \
           "have UserQuota foreign key relation. This management command can be run on an " \
           "as-needed basis."
    # TODO modify or get rid of this command

    def handle(self, *args, **options):
        users = User.objects.filter(is_active=True).filter(is_superuser=False).all()
        hs_internal_zone = "hydroshare"
        for u in users:
            uq = UserQuota.objects.filter(user__username=u.username, zone=hs_internal_zone).first()
            if not uq:
                # create default UserQuota object for this user
                new_uq = UserQuota.objects.create(user=u)
                new_uq.save()
