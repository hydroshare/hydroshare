"""
Check tracking functions for proper output.
"""
from django.core.management.base import BaseCommand
from hs_tracking.models import Variable
from hs_core.models import BaseResource
from hs_core.hydroshare import get_resource_by_shortkey


class Command(BaseCommand):
    help = "check on tracking"

    def add_arguments(self, parser):
        parser.add_argument('resource_id', type=str, help='username to check')
        parser.add_argument('--days', type=int, dest='days', default=31,
                            help='number of days to list')
        parser.add_argument('--users', type=int, dest='n_users', default=5,
                            help='number of users to return')

    def handle(self, *args, **options):
        resource_id = options['resource_id']
        days = options['days']
        n_users = options['n_users']

        try:
            resource = get_resource_by_shortkey(resource_id, or_404=False)
        except BaseResource.DoesNotExist:
            print("resource '{}' not found".format(resource_id))
            exit(1)

        recent = Variable.recent_users(resource,  days=days, n_users=n_users)
        for v in recent:
            print("username={} last_access={}"
                  .format(v.username, v.last_accessed.strftime("%Y-%m-%d %H:%M:%S")))
