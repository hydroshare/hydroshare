from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Reset quota by forcing recalculation of quota for all users."

    def handle(self, *args, **options):
        istorage = IrodsStorage()
        # reset quota for user zone
        user_root_path = '/{}/home/{}'.format(settings.HS_USER_IRODS_ZONE, settings.HS_IRODS_PROXY_USER_IN_USER_ZONE)
        istorage.setAVU(user_root_path, 'resetQuotaDir', 1)
