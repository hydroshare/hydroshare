from django.core.management.base import BaseCommand

from hs_core.models import BaseResource

class Command(BaseCommand):
    help = "Add quotaUserName AVU to all resources in iRODS as needed"

    def handle(self, *args, **options):
        resources = BaseResource.objects.all()
        for res in resources:
            istorage = res.get_irods_storage()
            istorage.setAVU(res.root_path, "quotaUserName", res.creator.username)