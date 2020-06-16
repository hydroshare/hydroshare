from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_tracking.models import Variable
from django.db.models import Max


def user_resource_matrix(fromdate, todate):
    """ return a list of (username, resource_id, last_access_timestamp), which
        shows the latest time that a user accessed a resource during the given
        period.
        :param fromdate (date type), the start date of the time period
        :param todate (date, type), the end date of the time period
    """
    users = User.objects.filter(
        visitor__session__variable__timestamp__gte=fromdate,
        visitor__session__variable__timestamp__lte=todate)\
            .distinct()
    events = []
    for u in users:
        resources = BaseResource.objects.filter(
                variable__timestamp__gte=fromdate,
                variable__timestamp__lte=todate,
                variable__session__visitor__user=u)
        for r in resources:
            latest = Variable.objects.filter(
                    resource=r,
                    session__visitor__user=u,
                    timestamp__gte=fromdate,
                    timestamp__lte=todate)\
                    .aggregate(latest=Max('timestamp'))

            events.append((u.username, r.short_id, latest['latest']))

    return events
