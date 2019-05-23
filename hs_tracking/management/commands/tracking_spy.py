"""
Check on tracking function.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.contrib.auth.models import User
from hs_tracking.models import Variable
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = "check on tracking"

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, dest='days', help='number of days to list')
        parser.add_argument('--resource', type=str, dest='resource', help='resource to list')
        parser.add_argument('--username', type=str, dest='username', help='username to list')

    def handle(self, *args, **options):
        days = options['days']
        username = options['username']
        resource = options['resource']

        if days is None:
            days = 31

        if username is not None:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                print("username '{}' not found".format(username))
                exit(1)
        else:
            user = None

        if user is not None and resource is not None:
            query = Q(resource_id=resource, session__visitor__user=user,
                      timestamp__gte=(datetime.now() - timedelta(days)))
        elif user is not None:
            query = Q(session__visitor__user=user,
                      timestamp__gte=(datetime.now() - timedelta(days)))
        elif resource is not None:
            query = Q(resource_id=resource,
                      timestamp__gte=(datetime.now() - timedelta(days)))
        else:
            query = Q(timestamp__gte=(datetime.now() - timedelta(days)))

        print("querying for records in last {} days".format(days))
        for v in Variable.objects.filter(query):
            time = v.timestamp.strftime('%Y-%m-%dT%H:%M:%S')
            print("{} name={} resource_id={} landing={} rest={} internal={} value={}"
                  .format(time, v.name, v.last_resource_id,
                          v.landing, v.rest, v.internal, v.value))
