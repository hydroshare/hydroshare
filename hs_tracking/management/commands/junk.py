"""
Check tracking functions for proper output.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from hs_tracking.models import Variable
from django.db.models import F, Q, Count, Max, Subquery
from datetime import datetime, timedelta
from hs_core.models import BaseResource


def user_resource_matrix(firstday, lastday):
    #     events = Variable.objects\
    #         .filter(
    #             timestamp__gte=(datetime.now()-timedelta(firstday)),
    #             timestamp__lte=(datetime.now()-timedelta(lastday)),
    #             resource__isnull=False,
    #             session__visitor__user__isnull=False)\
    #         .annotate(user=F('session__visitor__user'))\
    #         .annotate(last_accessed=Max('timestamp'))\
    #         .filter(timestamp=Max('timestamp'))

    from pprint import pprint
    first = datetime.now()-timedelta(firstday)
    last = datetime.now()-timedelta(lastday)
    users = User.objects.filter(
        visitor__session__variable__timestamp__gte=first,
        visitor__session__variable__timestamp__lte=last)\
            .distinct()
    events = []
    for u in users:
        resources = BaseResource.objects.filter(
                variable__timestamp__gte=first,
                variable__timestamp__lte=last,
                variable__session__visitor__user=u)
        for r in resources:
            latest = Variable.objects.filter(
                    resource=r, 
                    session__visitor__user=u, 
                    timestamp__gte=first,
                    timestamp__lte=last)\
                    .aggregate(latest=Max('timestamp'))
            
            events.append((u, r, latest['latest']))

    return events

class Command(BaseCommand):
    help = "check on tracking"

    def add_arguments(self, parser):
        parser.add_argument('--firstday', type=int, dest='firstday', default=365,
                            help='first day to list')
        parser.add_argument('--lastday', type=int, dest='lastday', default=365-30,
                            help='last day to list')

    def handle(self, *args, **options):
        firstday = options['firstday']
        lastday = options['lastday']

        triples = user_resource_matrix(firstday, lastday)
        for v in triples:
            print("last_accessed={} user_id={} short_id={}"
                  .format(v[2], v[0], v[1]))
