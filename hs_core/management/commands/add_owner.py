""" Add an owner to a resource or resources

Usage: add_owner {username} {resource list}
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models.privilege import UserResourcePrivilege, PrivilegeCodes


class Command(BaseCommand):
    help = "add owner to resource"

    def add_arguments(self, parser):

        parser.add_argument('new_owner', type=str)
        # a list of resource id's: none does nothing.
        parser.add_argument('resource_ids', nargs='*', type=str)

    def handle(self, *args, **options):
        user = User.objects.get(username=options['new_owner'])
        admin = User.objects.get(username='admin')

        if len(options['resource_ids']) > 0:  # an array of resource short_id to check.

            for rid in options['resource_ids']:
                resource = get_resource_by_shortkey(rid)
                UserResourcePrivilege.share(user=user,
                                            resource=resource,
                                            privilege=PrivilegeCodes.OWNER,
                                            grantor=admin)
                print("added owner {} to {}".format(options['new_owner'], rid))
        else:
            print("No resource list specified.")
