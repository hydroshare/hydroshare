from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from hs_access_control.models.privilege import UserResourcePrivilege
from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes


class Command(BaseCommand):
    """
    Migrate published resources to published user quota holder
    """
    help = "Migrate published resources to published user quota holder"

    def handle(self, *args, **options):
        published_user = User.objects.get(username=settings.PUBLISHED_USER)
        resources = BaseResource.objects.filter(raccess__published=True).exclude(quota_holder=published_user)
        count = 0
        for res in resources:
            print('Fixing resource: {}'.format(res.short_id))
            try:
                UserResourcePrivilege.share(user=published_user, resource=res,
                                            privilege=PrivilegeCodes.OWNER, grantor=res.quota_holder)
                res.set_quota_holder(res.quota_holder, published_user)
            except Exception as ex:
                print(res.short_id + ' raised SessionException when setting quota holder: '
                      + ex)
                continue

        print('{} resources with missing quota holder have been fixed'.format(count))
