import csv
import datetime
import sys
import logging
from calendar import monthrange

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from hs_core.models import BaseResource
from theme.models import UserProfile

from ... import models as hs_tracking

# Add logger for stderr messages.
err = logging.getLogger('stats-command')
err.setLevel(logging.ERROR)
handler = logging.StreamHandler(stream=sys.stderr)
formatter = logging.Formatter("%(asctime)s - "
                              "%(levelname)s - "
                              "%(funcName)s - "
                              "line %(lineno)s - "
                              "%(message)s")
handler.setFormatter(formatter)
err.addHandler(handler)


def month_year_iter(start, end):
    ym_start = 12 * start.year + start.month - 1
    ym_end = 12 * end.year + end.month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        m += 1
        d = monthrange(y, m)[1]
        yield timezone.datetime(y, m, d, tzinfo=timezone.pytz.utc)


class Command(BaseCommand):
    help = "Output engagement stats about HydroShare"

    def add_arguments(self, parser):

        parser.add_argument(
            "--monthly-users-counts",
            dest="monthly_users_counts",
            action="store_true",
            help="user stats by month",
        )
        parser.add_argument(
            "--monthly-orgs-counts",
            dest="monthly_orgs_counts",
            action="store_true",
            help="unique organization stats by month",
        )
        parser.add_argument(
            "--users-details",
            dest="users_details",
            action="store_true",
            help="current user list",
        )
        parser.add_argument(
            "--resources-details",
            dest="resources_details",
            action="store_true",
            help="current resource list with sizes",
        )
        parser.add_argument(
            "--monthly-users-by-type",
            dest="monthly_users_by_type",
            action="store_true",
            help="user type stats by month",
        )
        parser.add_argument(
            "--yesterdays-variables",
            dest="yesterdays_variables",
            action="store_true",
            help="dump tracking variables collected today",
        )
        parser.add_argument('lookback-days', nargs='?', default=1)

    def print_var(self, var_name, value, period=None):
        timestamp = timezone.now()
        if not period:
            print("{}: {} {}".format(timestamp, var_name, value))
        else:
            start, end = period
            print("{}: ({}/{}--{}/{}) {} {}".format(timestamp,
                                                    start.year, start.month,
                                                    end.year, end.month,
                                                    var_name, value))

    def monthly_users_counts(self, start_date, end_date):
        profiles = User.objects.filter(date_joined__lte=end_date, is_active=True)
        self.print_var("monthly_users_counts", profiles.count(),
                       (start_date, end_date))

    def monthly_orgs_counts(self, start_date, end_date):
        profiles = UserProfile.objects.filter(user__date_joined__lte=end_date)
        org_count = profiles.values('organization').distinct().count()
        self.print_var("monthly_orgs_counts", org_count, (start_date, end_date))

    def monthly_users_by_type(self, start_date, end_date):
        user_types = UserProfile.objects.values('user_type').distinct()
        for ut in [_['user_type'] for _ in user_types]:
            ut_users = User.objects.filter(userprofile__user_type=ut)
            sessions = hs_tracking.Session.objects.filter(
                Q(begin__gte=start_date) &
                Q(begin__lte=end_date) &
                Q(visitor__user__in=ut_users)
            )
            self.print_var("active_{}".format(ut),
                           sessions.count(), (end_date, start_date))

    def users_details(self):
        w = csv.writer(sys.stdout)
        fields = [
            'created date',
            'first name',
            'last name',
            'email',
            'user type',
            'organization',
            'last login',
            'user id',
        ]
        w.writerow(fields)
        for up in UserProfile.objects.filter(user__is_active=True):
            last_login = up.user.last_login.strftime('%m/%d/%Y') if up.user.last_login else ""
            values = [
                up.user.date_joined.strftime('%m/%d/%Y %H:%M:%S.%f'),
                up.user.first_name,
                up.user.last_name,
                up.user.email,
                up.user_type,
                up.organization,
                last_login,
                up.user_id,
            ]
            w.writerow([unicode(v).encode("utf-8") for v in values])

    def resources_details(self):
        w = csv.writer(sys.stdout)
        fields = [
            'creation date',
            'title',
            'resource type',
            'size',
            'publication status',
            'user type',
            'user id'
        ]
        w.writerow(fields)
        failed_resource_ids = []
        for r in BaseResource.objects.all():
            try:
                values = [
                    r.metadata.dates.get(type="created").
                    start_date.strftime("%m/%d/%Y %H:%M:%S.%f"),
                    r.metadata.title.value,
                    r.resource_type,
                    r.size,
                    r.raccess.sharing_status,
                    r.user.userprofile.user_type,
                    r.user_id
                ]
                w.writerow([unicode(v).encode("utf-8") for v in values])

            except Exception as e:
                err.error(e)

                # save the id of the broken resource
                failed_resource_ids.append(r.short_id)

        # print all failed resources for debugging purposes
        for f in failed_resource_ids:
            err.error('Error processing resource: %s' % f)

    def yesterdays_variables(self, lookback=1):

        today_start = timezone.datetime.now().replace(
           hour=0,
           minute=0,
           second=0,
           microsecond=0)

        # adjust start date for look-back option
        yesterday_start = today_start - datetime.timedelta(days=lookback)
        variables = hs_tracking.Variable.objects.filter(
            timestamp__gte=yesterday_start,
            timestamp__lt=today_start
        )
        for v in variables:
            uid = v.session.visitor.user.id if v.session.visitor.user else None

            # make sure values are | separated (i.e. replace legacy format)
            vals = self.dict_spc_to_pipe(v.value)

            # encode variables as key value pairs (except for timestamp)
            values = [unicode(v.timestamp).encode('utf-8'),
                      'user_id=%s' % unicode(uid).encode(),
                      'session_id=%s' % unicode(v.session.id).encode(),
                      'action=%s' % unicode(v.name).encode(),
                      vals]
            print('|'.join(values))

    def dict_spc_to_pipe(self, s):

        # exit early if pipes already exist
        if '|' in s:
            return s

        # convert from space separated to pipe separated
        groups = s.split('=')

        # need to take into account possible spaces in the dict values
        formatted_str = ''
        for i in range(1, len(groups)):
            k = groups[i-1].split(' ')[-1]
            if i < len(groups) - 1:
                v = ' '.join(groups[i].split(' ')[:-1])
                formatted_str += '%s=%s|' % (k, v)
            else:
                v = ' '.join(groups[i].split(' ')[:])
                formatted_str += '%s=%s' % (k, v)
        return formatted_str

    def handle(self, *args, **options):
        START_YEAR = 2016
        start_date = timezone.datetime(START_YEAR, 1, 1).date()
        end_date = timezone.datetime.now().replace(hour=0,
                                                   minute=0,
                                                   second=0,
                                                   microsecond=0)

        if options["monthly_users_counts"]:
            for month_end in month_year_iter(start_date, end_date):
                self.monthly_users_counts(start_date, month_end)
        if options["monthly_orgs_counts"]:
            for month_end in month_year_iter(start_date, end_date):
                self.monthly_orgs_counts(start_date, month_end)
        if options["users_details"]:
            self.users_details()
        if options["monthly_users_by_type"]:
            for month_end in month_year_iter(start_date, end_date):
                month_start = month_end.replace(day=1)
                self.monthly_users_by_type(month_start, month_end)
        if options["resources_details"]:
            self.resources_details()
        if options["yesterdays_variables"]:
            self.yesterdays_variables(lookback=int(options['lookback-days']))
