from django.core.management.base import BaseCommand
from django.db.models import Q
from django.contrib.auth.models import User

from ... import models as hs_tracking

from theme.models import UserProfile

from django.utils import timezone
from calendar import monthrange

def date_range(date):
    first_day = date.replace(day = 1)
    last_day = date.replace(day = calendar.monthrange(date.year, date.month)[1])
    return first_day, last_day

def month_year_iter(start, end):
    #http://stackoverflow.com/questions/5734438/how-to-create-a-month-iterator
    ym_start = 12 * start.year + start.month - 1
    ym_end = 12 * end.year + end.month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        m += 1
        d = monthrange(y, m)[1]
        yield timezone.datetime(y, m, d, tzinfo=timezone.pytz.utc)

class Command(BaseCommand):
    help = "Output daily stats"

    def print_var(self, var_name, value, period=None):
        timestamp = timezone.now()
        if not period:
            print("{}: {} {}".format(timestamp, var_name, value))
        else:
            start, end = period
            print("{}: ({}/{}--{}/{}) {} {}".format(timestamp, start.year, start.month, end.year, end.month, var_name, value))

    def daily_users_report(self, start_date, end_date):
        profiles = UserProfile.objects.filter(user__date_joined__lte=date)
        self.print_var("all_users", profiles.count(), (date, date))
        self.print_var("all_orgs", profiles.values('organization').distinct().count(), (date, date))

    def active_users_by_type_report(self, start_date, end_date):
        #Active user type,Number of active users, Number of resources created, Number of resources downloaded, Number of logons 
        date_filtered = UserProfile.objects.filter(user__date_joined__lte=end_date)
        for ut in [_['user_type'] for _ in UserProfile.objects.values('user_type').distinct()]:
            ut_profiles = UserProfile.objects.filter(user_type=ut)
	    ut_users = [p.user for p in ut_profiles]
            sessions = hs_tracking.Session.objects.filter(Q(begin__gte=start_date) & Q(begin__lte=end_date) & Q(visitor__user__in=ut_users))
            self.print_var("active_{}".format(ut), sessions.count(), (end_date, start_date))


    def handle(self, *args, **options):
        start_date = timezone.datetime(2016, 1, 1).date()
        end_date = timezone.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        for month_end in month_year_iter(start_date, end_date):
            #self.daily_users_report(month_end)
	    month_start = timezone.datetime(month_end.year, month_end.month, 1, 0, 0, tzinfo=timezone.pytz.utc)
            self.active_users_by_type_report(month_start, month_end)
