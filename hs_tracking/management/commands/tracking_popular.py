"""
Check tracking functions for proper output.
"""
from django.core.management.base import BaseCommand
from hs_tracking.models import Variable


class Command(BaseCommand):
    help = "check on tracking"

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, dest='days', default=31,
                            help='number of days to list')
        parser.add_argument('--resources', type=int, dest='n_resources', default=5,
                            help='number of resources to return')

    def handle(self, *args, **options):
        days = options['days']
        n_resources = options['n_resources']

        popular = Variable.popular_resources(days=days, n_resources=n_resources)
        for v in popular:
            print("users={} short_id={}"
                  .format(v.users, v.short_id))
            print("  title={}".format(v.title))
            print("  created={} updated={}"
                  .format(v.created.strftime("%Y-%m-%d %H:%M:%S"),
                          v.last_updated.strftime("%Y-%m-%d %H:%M:%S")))
            print("  published={} public={} discoverable={} first author={}"
                  .format(v.published,
                          v.public,
                          v.discoverable,
                          v.first_creator))
