"""
This prints the active permissions of an access control relationship between a user and a resource.
This is invaluable for access control debugging.

"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models.utilities import coarse_permissions
from hs_access_control.management.utilities import user_from_name


def usage():
    print("Permissions usage:")
    print("  permissions {username} {resource-id}")
    print("Where:")
    print("  {username} is a user name.")
    print("  {resource-id} is a 32-character resource guid.")


class Command(BaseCommand):
    help = """Print access control provenance."""

    def add_arguments(self, parser):

        # a command to execute
        parser.add_argument('username', type=str)
        parser.add_argument('resource_id', type=str)

    def handle(self, *args, **options):

        if options['username'] is None or options['resource_id'] is None:
            usage()
            exit(1)

        username = options['username']
        resource_id = options['resource_id']

        user = user_from_name(username)
        if user is None:
            usage()
            exit(1)

        try:
            resource = get_resource_by_shortkey(resource_id, or_404=False)
        except BaseResource.DoesNotExist:
            print("No such resource {}.".format(resource_id))
            usage()
            exit(1)

        print(coarse_permissions(user, resource))
