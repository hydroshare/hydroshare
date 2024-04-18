from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage
from django.conf import settings


class Command(BaseCommand):
    help = "Reset quota by forcing quota iRODS microservices to recalculate quota for all users."

    def handle(self, *args, **options):
        # TODO: Update this script
        # Also add a management command to read quota holders from irods avu and store in the django db resource model
        istorage = IrodsStorage()
        # reset quota for data zone
        root_path = '/{}/home/{}'.format(settings.IRODS_ZONE, settings.IRODS_USERNAME)
        istorage.setAVU(root_path, 'resetQuotaDir', 1)
        # reset quota for user zone
        user_root_path = '/{}/home/{}'.format(settings.HS_USER_IRODS_ZONE, settings.HS_IRODS_PROXY_USER_IN_USER_ZONE)
        istorage.setAVU(user_root_path, 'resetQuotaDir', 1)
