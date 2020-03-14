"""
Remove things from the CZO National group that should be part of other groups alone.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_core.models import BaseResource
from hs_access_control.models import GroupResourcePrivilege


class Command(BaseCommand):
    help = "CZO national group should not contain resources in other CZO groups"

    def handle(self, *args, **options):
        user = User.objects.get(username='czo_national')
        national = Group.objects.get(name='CZO National')

        resources = BaseResource.objects.filter(r2grp__group=national)\
                                        .exclude(title__startswith='Cross-CZO')
        print("there are {} resources".format(resources.count()))
        for r in resources:
            print("unsharing resource {} with national".format(r.title.encode('ascii', 'ignore')))
            GroupResourcePrivilege.unshare(resource=r, group=national, grantor=user)
