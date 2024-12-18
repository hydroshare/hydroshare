from django.core.management.base import BaseCommand

from hs_access_control.models.user import UserResourcePermission
from hs_access_control.models.privilege import UserResourcePrivilege, GroupResourcePrivilege

class Command(BaseCommand):
    help = "Creates/Updates records in UserResourcePermission model - the denormalized model for user permission on resource"

    def handle(self, *args, **options):
        for urp in UserResourcePrivilege.objects.iterator():
            UserResourcePermission.update_on_user_resource_update(user=urp.user, resource=urp.resource)
        for grp in GroupResourcePrivilege.objects.iterator():
            UserResourcePermission.update_on_group_resource_update(group=grp.group, resource=grp.resource)

        record_count = UserResourcePermission.objects.count()
        print(f"Total records added or updated in UserResourcePermission model:{record_count}", flush=True)