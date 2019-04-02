"""
Check tracking functions for proper output.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_tracking.models import Variable


class Command(BaseCommand):
    help = "check on tracking"

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='username to check')
        parser.add_argument('--days', type=int, dest='days', default=31,
                            help='number of days to list')
        parser.add_argument('--resources', type=int, dest='resources', default=5,
                            help='number of resources to return')

    def handle(self, *args, **options):
        username = options['username']
        days = options['days']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print("username '{}' not found".format(username))
            exit(1)

        recent = Variable.recent_resources(user, days)
        for v in recent:
            print("last_access={} resource_id={}"
                  .format(v['last_accessed'].strftime("%Y-%m-%d %H:%M:%S"),
                          v['resource_id']))
