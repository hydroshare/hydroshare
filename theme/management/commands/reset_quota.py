from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage
from django.conf import settings


class Command(BaseCommand):
    help = "Reset quota by forcing quota iRODS microservices to recalculate quota for all users."

    def handle(self, *args, **options):
        istorage = IrodsStorage()
        # reset quota for data zone
        root_path = '/{}/home/{}'.format(settings.IRODS_ZONE, settings.IRODS_USERNAME)
        istorage.set_metadata(root_path, 'resetQuotaDir', 1)
        # reset quota for user zone
        user_root_path = '/{}/home/{}'.format(settings.HS_USER_IRODS_ZONE, settings.HS_IRODS_PROXY_USER_IN_USER_ZONE)
        istorage.set_metadata(user_root_path, 'resetQuotaDir', 1)
