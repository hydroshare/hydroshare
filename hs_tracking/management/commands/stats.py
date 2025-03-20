import csv
import datetime
import sys
import logging
import pytz
import warnings
from calendar import monthrange

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from hs_core.models import BaseResource, Date
from hs_core.hydroshare import current_site_url
from theme.models import UserProfile

from ... import models as hs_tracking

warnings.filterwarnings("ignore", category=RuntimeWarning)

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

SITE_URL = current_site_url()


def month_year_iter(start, end):
    ym_start = 12 * start.year + start.month - 1
    ym_end = 12 * end.year + end.month - 1
    for ym in range(ym_start, ym_end):
        y, m = divmod(ym, 12)
        m += 1
        d = monthrange(y, m)[1]
        yield timezone.datetime(y, m, d, tzinfo=pytz.UTC)


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
        parser.add_argument(
            "--publications-between-dates",
            dest="publications_between_dates",
            action="store_true",
            help="show publication stats between two dates: --start-date YYYY-MM-DD --end-date YYYY-MM-DD",
        )
        parser.add_argument(
            "--start-date",
            dest="start_date",
            help="start date for publication stats, format: YYYY-MM-DD",
            default=timezone.datetime(2016, 1, 1, tzinfo=pytz.UTC).date().strftime('%Y-%m-%d'),
        )
        parser.add_argument(
            "--end-date",
            dest="end_date",
            help="end date for publication stats, format: YYYY-MM-DD",
            default=timezone.datetime.now().replace(hour=0,
                                                    minute=0,
                                                    second=0,
                                                    microsecond=0).strftime('%Y-%m-%d'),
        )
        parser.add_argument(
            "--publications-by-year",
            dest="publications_by_year",
            action="store_true",
            help="show publications by year since 2016",
        )
        parser.add_argument(
            "--verbose",
            dest="verbose",
            action="store_true",
            help="print verbose output",
        )
        parser.add_argument('lookback-days', nargs='?', default=1)

    def print_var(self, var_name, value, period=None):
        timestamp = timezone.now()
        if not period:
            print("{}: {} {}".format(timestamp, var_name, value))
        else:
            start, end = period
            print(("{}: ({}/{}--{}/{}) {} {}".format(timestamp,
                                                     start.year, start.month,
                                                     end.year, end.month,
                                                     var_name, value)))

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
                Q(begin__gte=start_date)
                & Q(begin__lte=end_date)
                & Q(visitor__user__in=ut_users)
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
            w.writerow([str(v) for v in values])

    def resources_details(self):
        w = csv.writer(sys.stdout)
        fields = [
            'creation date',
            'title',
            'resource type',
            'size',
            'publication status',
            'user type',
            'user id',
            'resource id',
            'publication date',
            'bag last downloaded date',
            'resource updated date',
            'last updated by user id'
        ]
        w.writerow(fields)
        failed_resource_ids = []
        for r in BaseResource.objects.all():
            try:
                pub_date = r.metadata.dates.get(type='published')\
                    .start_date.strftime("%m/%d/%Y %H:%M:%S.%f")
            except Date.DoesNotExist:
                pub_date = None
            try:
                last_downloaded = r.bag_last_downloaded
                if last_downloaded:
                    last_downloaded = last_downloaded.strftime("%m/%d/%Y %H:%M:%S.%f")
                else:
                    last_downloaded = None
                last_changed_by = r.last_changed_by
                if last_changed_by:
                    last_changed_by = last_changed_by.id
                else:
                    last_changed_by = None
                updated_date = r.updated.strftime("%m/%d/%Y %H:%M:%S.%f")
                values = [
                    r.metadata.dates.get(type="created").
                    start_date.strftime("%m/%d/%Y %H:%M:%S.%f"),
                    r.metadata.title.value,
                    r.resource_type,
                    r.size,
                    r.raccess.sharing_status,
                    r.user.userprofile.user_type,
                    r.user_id,
                    r.short_id,
                    pub_date,
                    last_downloaded,
                    updated_date,
                    last_changed_by
                ]
                w.writerow([str(v) for v in values])

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
            values = [str(v.timestamp),
                      'user_id=%s' % str(uid),
                      'session_id=%s' % str(v.session.id),
                      'action=%s' % str(v.name),
                      vals]
            print('|'.join(values))

    def publications_between_dates(self, start_date, end_date, options):
        '''
        Print publication stats between start and end dates
        '''

        def print_resource_info_from_dates(dates):
            for d in dates:
                print("-" * 80)
                try:
                    print(f"Date: {d}")
                    print(f"Associated Title: {d.content_object.title}")
                    rid = d.content_object.citation.first().value
                    print(f"Associated Resource: {SITE_URL}resource/{rid}")
                except Exception as e:
                    print("Error inspecting date: ", e)
                    pass
            print("*" * 80)
        public_count = 0
        private_count = 0
        bad_count = 0
        print(f"Publications between {start_date} and {end_date}")
        dates = Date.objects.filter(type='created', start_date__range=[start_date, end_date])
        bad_dates = []
        for d in dates.all():
            try:
                d.metadata.resource.raccess
            except Exception:
                bad_count = bad_count + 1
                bad_dates.append(d)
                continue
            if d.metadata.resource.raccess.public is True:
                public_count = public_count + 1
            else:
                private_count = private_count + 1
        published_dates = Date.objects.filter(type='published', start_date__range=[start_date, end_date])
        print(f"resources that became published within date range: {published_dates.count()}")
        if options.get("verbose"):
            print(f"resources that were created within date range: {dates.count()}")
            print(f"resources that were created in the date range that are currently private: {private_count}")
            print(f"resources that were created in the date range that are currently public:{public_count}")
            print(f"resources that can't be checked because they have no metadata: {bad_count}")
            print("*" * 80)
            print("Published Date Information")
            print_resource_info_from_dates(published_dates)
            print("*" * 80)
            print("Information for 'Bad Dates' discovered")
            print_resource_info_from_dates(bad_dates)

    def publications_by_year(self, options):
        '''
        Print publication stats by year since 2016
        '''
        START_YEAR = 2016
        for y in range(START_YEAR, timezone.now().year + 1):
            if y == timezone.now().year:
                print("Year to date:")
            else:
                print(f"Year {y}:")
            self.publications_between_dates(start_date=f"{y}-01-01", end_date=f"{y}-12-31", options=options)
            print("#" * 80)
            print()

    def dict_spc_to_pipe(self, s):

        # exit early if pipes already exist
        if '|' in s:
            return s

        # convert from space separated to pipe separated
        groups = s.split('=')

        # need to take into account possible spaces in the dict values
        formatted_str = ''
        for i in range(1, len(groups)):
            k = groups[i - 1].split(' ')[-1]
            if i < len(groups) - 1:
                v = ' '.join(groups[i].split(' ')[:-1])
                formatted_str += '%s=%s|' % (k, v)
            else:
                v = ' '.join(groups[i].split(' ')[:])
                formatted_str += '%s=%s' % (k, v)
        return formatted_str

    def handle(self, *args, **options):
        # check for start_date and end_date as args
        # cant have start/end in addition to lookback
        if 'lookback-days' in options:
            if 'start_date' in options or 'end_date' in options:
                print("Lookback days option will be ignored")
        start_date = options.get("start_date", timezone.datetime(2016, 1, 1, tzinfo=pytz.UTC).strftime('%Y-%m-%d'))
        end_date = options.get("end_date", timezone.datetime.now().replace(hour=0,
                                                                           minute=0,
                                                                           second=0,
                                                                           microsecond=0).strftime('%Y-%m-%d'))
        if options["publications_between_dates"]:
            self.publications_between_dates(start_date, end_date, options=options)
        if options["publications_by_year"]:
            self.publications_by_year(options=options)
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
