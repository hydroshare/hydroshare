from django.core.management.base import BaseCommand
from django_irods.storage import IrodsStorage
from django.conf import settings


class Command(BaseCommand):
    help = "Reset quota by forcing quota iRODS microservices to recalculate quota for all users."

    def handle(self, *args, **options):
        istorage = IrodsStorage()
        root_path = '/{}/home/{}'.format(settings.IRODS_ZONE, settings.IRODS_USERNAME)
        istorage.setAVU(root_path, 'resetQuotaDir', 1)
