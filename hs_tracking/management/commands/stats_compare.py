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
            "--resources-details",
            dest="resources_details",
            action="store_true",
            help="current resource list with sizes",
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
        parser.add_argument(
            "--compare",
            dest="compare",
            action="store_true",
            help="compare the resources_details command with the publications_by_year command",
        )

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
                    rid = d.metadata.resource.short_id
                    print(f"Associated Resource: {SITE_URL}/resource/{rid}")
                except Exception as e:
                    print("Error inspecting date: ", e)
                    pass
            print("*" * 80)
        published_dates = Date.objects.filter(type='published', start_date__range=[start_date, end_date])
        print(f"resources that became published within date range: {published_dates.count()}")

        if options.get("verbose"):
            public_count = 0
            private_count = 0
            bad_count = 0
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
                end_date = timezone.now().strftime('%Y-%m-%d')
            else:
                print(f"Year {y}:")
                end_date = f"{y}-12-31"
            self.publications_between_dates(start_date=f"{y}-01-01", end_date=end_date, options=options)
            print("#" * 80)
            print()

    def compare(self, start_date, end_date, options):
        '''
        Compare numbers of published resources using the resources_details command
        vs the publications_by_year command
        '''

        # get a list of resources that were published in the date range using the resources_details command
        resources_details_published_resources = []
        print("Getting resources that were published in the date range using the resources_details command")
        for r in BaseResource.objects.all():
            pub_date = None
            try:
                pub_date = r.metadata.dates.filter(type='published').first()
                if pub_date:
                    # check that it is in the date range
                    start_dt = timezone.datetime.strptime(start_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
                    end_dt = timezone.datetime.strptime(end_date, '%Y-%m-%d').replace(tzinfo=pytz.UTC)
                    pub_date = pub_date.start_date.replace(tzinfo=pytz.UTC)
                    if pub_date <= start_dt:
                        continue
                    if pub_date >= end_dt:
                        continue
                    pub_date = pub_date.strftime("%m/%d/%Y %H:%M:%S.%f")
            except Date.DoesNotExist:
                pass
            # print the type of start_date
            # convert start_date and end_date to datetime objects
            if pub_date:
                resources_details_published_resources.append(r)
                print(f"Resource: {SITE_URL}/resource/{r.short_id} was published on {pub_date}")
        print(f"resources that became published within date range: {len(resources_details_published_resources)}")
        print("#" * 80)
        print()

        # get a list of resources that were published in the date range using the publications_by_year command
        publications_by_year_published_resources = []
        dates_with_errors = []
        print("Getting resources that were published in the date range using the publications_by_year command")
        published_dates = Date.objects.filter(type='published', start_date__range=[start_date, end_date])
        for d in published_dates:
            try:
                rid = d.metadata.resource.short_id
                publications_by_year_published_resources.append(d.metadata.resource)
                print(f"Resource: {SITE_URL}/resource/{rid} was published on {d.start_date}")
            except Exception as e:
                print("Error inspecting date: ", e)
                dates_with_errors.append(d)
                pass

        print(f"resources that became published within date range: {len(publications_by_year_published_resources)}")
        # print the dates with errors
        print("Dates with errors:")
        for d in dates_with_errors:
            try:
                print(f"Date: {d}")
                print(f"Associated Title: {d.content_object.title}")
                rid = d.metadata.resource.short_id
                print(f"Associated Resource: {SITE_URL}/resource/{rid}")
            except Exception as e:
                print("Error inspecting date: ", e)
                pass
        print("#" * 80)
        print()
        # compare the two lists, print the differences
        resources_details_published_resources_set = set([r.short_id for r in resources_details_published_resources])
        publications_by_year_published_resources_set = set([r.short_id for r in publications_by_year_published_resources])
        print(f"resources_details_published_resources: {len(resources_details_published_resources_set)}")
        print(f"publications_by_year_published_resources: {len(publications_by_year_published_resources_set)}")
        # prin t the difference between the two sets
        diff = resources_details_published_resources_set - publications_by_year_published_resources_set
        if diff:
            print(f"resources that were published in the resources_details command but not in the publications_by_year command: {diff}")
        # print the difference between the two sets
        diff = publications_by_year_published_resources_set - resources_details_published_resources_set
        if diff:
            print(f"resources that were published in the publications_by_year command but not in the resources_details command: {diff}")

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
        if options["resources_details"]:
            self.resources_details()
        if options["compare"]:
            self.compare(start_date, end_date, options=options)
