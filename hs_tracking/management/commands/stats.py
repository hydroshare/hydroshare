import csv
import datetime
import sys
import logging
from calendar import monthrange
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from django_irods.icommands import SessionException
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

    option_list = BaseCommand.option_list + (
        make_option(
            "--monthly-users-counts",
            dest="monthly_users_counts",
            action="store_true",
            help="user stats by month",
        ),
        make_option(
            "--monthly-orgs-counts",
            dest="monthly_orgs_counts",
            action="store_true",
            help="unique organization stats by month",
        ),
        make_option(
            "--users-details",
            dest="users_details",
            action="store_true",
            help="current user list",
        ),
        make_option(
            "--resources-details",
            dest="resources_details",
            action="store_true",
            help="current resource list with sizes",
        ),
        make_option(
            "--monthly-users-by-type",
            dest="monthly_users_by_type",
            action="store_true",
            help="user type stats by month",
        ),
        make_option(
            "--yesterdays-variables",
            dest="yesterdays_variables",
            action="store_true",
            help="dump tracking variables collected today, test",
        ),
    )

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
        ]
        w.writerow(fields)

        for up in UserProfile.objects.filter(user__is_active=True):
            last_login = up.user.last_login.strftime('%m/%d/%Y') if up.user.last_login else ""
            values = [
                up.user.date_joined.strftime('%m/%d/%Y'),
                up.user.first_name,
                up.user.last_name,
                up.user.email,
                up.user_type,
                up.organization,
                last_login,
            ]
            w.writerow([unicode(v).encode("utf-8") for v in values])

    def resources_details(self):
        w = csv.writer(sys.stdout)
        fields = [
            'creation date',
            'title',
            'resource type',
            'size',
            'publication status'
        ]
        w.writerow(fields)

        resources = BaseResource.objects.all()
        for r in resources:
            total_file_size = 0
            try:
                f_sizes = [f.resource_file.size
                           if f.resource_file else 0
                           for f in r.files.all()]
                total_file_size += sum(f_sizes)

                fed_f_sizes = [int(f.fed_resource_file_size)
                               if f.fed_resource_file_size else 0
                               for f in r.files.all()]
                total_file_size += sum(fed_f_sizes)
            except SessionException as e:
                # write the error to stderr
                err.error(e)

            values = [
                r.metadata.dates.get(type="created").start_date.strftime("%m/%d/%Y"),
                r.metadata.title.value,
                r.resource_type,
                total_file_size,
                r.raccess.sharing_status,
            ]
            w.writerow([unicode(v).encode("utf-8") for v in values])

    def yesterdays_variables(self):
        w = csv.writer(sys.stdout)
        fields = [
            'timestamp',
            'user id',
            'session id',
            'name',
            'type',
            'value',
        ]
        w.writerow(fields)

        today_start = timezone.datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        yesterday_start = today_start - datetime.timedelta(days=1)
        variables = hs_tracking.Variable.objects.filter(
            timestamp__gte=yesterday_start,
            timestamp__lt=today_start
        )
        for v in variables:
            uid = v.session.visitor.user.id if v.session.visitor.user else None
            values = [
                v.timestamp,
                uid,
                v.session.id,
                v.name,
                v.type,
                v.value,
            ]
            w.writerow([unicode(v).encode("utf-8") for v in values])

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
            self.yesterdays_variables()
