from django.core.management.base import BaseCommand

from hs_core.models import BaseResource


class Command(BaseCommand):
    help = "Add quotaUserName AVU to all resources in iRODS as needed"

    def handle(self, *args, **options):
        resources = BaseResource.objects.all()
        for res in resources:
            # if quota_holder is not set for the resource, set it to resource's creator
            if not res.get_quota_holder():
                res.set_quota_holder(res.creator)
