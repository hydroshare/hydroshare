""" Add an owner to a resource or resources

Usage: add_owner {username} {resource list}
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models.privilege import UserResourcePrivilege, PrivilegeCodes


class Command(BaseCommand):
    help = "add owner to resource"

    def add_arguments(self, parser):

        parser.add_argument('new_owner', type=str)

        parser.add_argument(
            '--owned_by',
            dest='owned_by',
            help='prior owner of the resources'
        )

        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        user = User.objects.get(username=options['new_owner'])
        admin = User.objects.get(username='admin')

        if options['owned_by'] is not None:
            prior = User.objects.get(username=options['owned_by'])
            for res in BaseResource.objects.filter(r2urp__user=prior,
                                                   r2urp__privilege=PrivilegeCodes.OWNER):
                resource = get_resource_by_shortkey(res.short_id)
                UserResourcePrivilege.share(user=user,
                                            resource=resource,
                                            privilege=PrivilegeCodes.OWNER,
                                            grantor=admin)
                print("added owner {} to {}".format(options['new_owner'], resource.short_id))

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.

            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                UserResourcePrivilege.share(user=user,
                                            resource=resource,
                                            privilege=PrivilegeCodes.OWNER,
                                            grantor=admin)
                print("added owner {} to {}".format(options['new_owner'], rid))
