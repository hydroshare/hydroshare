"""Lists all the resources published in a given year.
"""
import csv as csv_module
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from django.db.models import F
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist


class Command(BaseCommand):
    help = "Print resource information"
    max_funders = 0
    rows = []

    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--year',
            dest='year',
            help='limit to resources published in a given year'
        )

        parser.add_argument('--days', type=int, dest='days', help='include resources updated in the last X days')

        parser.add_argument(
            '--type',
            dest='type',
            help='limit to resources of a particular type'
        )

        parser.add_argument(
            '--owned_by',
            dest='owned_by',
            help='limit to resources owned by specific user'
        )

        parser.add_argument(
            '--csv_dir',
            dest='csv_dir',
            help='directory in which to export csv'
        )

    def handle(self, *args, **options):
        days = options['days']
        resources = BaseResource.objects.filter(raccess__published=True)
        owner = options['owned_by']
        res_type = options['type']
        csv = options['csv_dir']
        year = options['year']
        file_name = ''

        if owner is not None:
            try:
                owner = User.objects.get(username=owner)
                resources.filter(r2urp__user=owner,
                                 r2urp__privilege=PrivilegeCodes.OWNER)
                if csv:
                    file_name += f"_owner={owner}"
            except ObjectDoesNotExist:
                print(f"User matching {owner} not found")

        if res_type is not None:
            if res_type in ["CompositeResource", "CollectionResource"]:
                resources.filter(resource_type=res_type)
                file_name += f"_restype={res_type}"
            else:
                print(f"Type {res_type} is not supported. Must be 'CompositeResource' or 'CollectionResource'")

        if csv:
            file_name += f"_run={timezone.now()}"
            if year:
                file_name += f"_year={year}"

        resources = resources.order_by(F('updated').asc(nulls_first=True))
        site_url = hydroshare.utils.current_site_url()

        if csv:
            full_file = f'{csv}/published_resources{file_name}.csv'
            if os.path.exists(full_file):
                raise OSError(f"File already exists at {full_file}")
            os.makedirs(os.path.dirname(full_file), exist_ok=True)
            self.csvfile = open(f'{csv}/published_resources{file_name}.csv', 'w+')
            self.writer = csv_module.writer(self.csvfile)

        for resource in resources:
            pub_date = self.get_publication_date(resource)
            if not pub_date:
                continue
            if year:
                if pub_date.year != int(year):
                    continue
            if days:
                cuttoff_time = timezone.now() - timedelta(days)
                if not pub_date >= cuttoff_time:
                    continue
            if csv:
                self.build_csv(resource, pub_date, site_url)
            else:
                self.print_resource(resource, pub_date, site_url)
        if csv:
            self.write_csv()

    def get_publication_date(self, resource):
        published_date = resource.metadata.dates.filter(type="published").first()
        if not published_date:
            print(f"Publication date not found for {resource.short_id}")
            return None
        return published_date.start_date

    def print_resource(self, res, pub_date, site_url):
        res_url = site_url + res.absolute_url
        funding_agencies = res.metadata.funding_agencies.all()
        print("\n")
        print("*" * 100)
        print(f"{res_url}")
        if res.doi:
            print(res.doi)
        else:
            print("Resource has no doi")
        print(res.metadata.title.value)
        print(f"Resource type: {res.resource_type}")
        if pub_date:
            print(f"Published on {pub_date}")
        else:
            print("Resource has no publication date")

        if funding_agencies:
            print(f"Found {len(funding_agencies)} funder(s):")
            for count, f in enumerate(funding_agencies, 1):
                print(f"--- Funder #{count} ---")
                if f.agency_name:
                    print(f"Agency name: {f.agency_name}")
                else:
                    print("No agency name")
                if f.agency_url:
                    print(f"Agency url: {f.agency_url}")
                else:
                    print("No agency url")
                if f.award_title:
                    print(f"Award title: {f.award_title}")
                else:
                    print("No award title")
                if f.award_number:
                    print(f"Award number: {f.award_number}")
                else:
                    print("No award number")
        else:
            print("Resource has no funding information")

    def build_csv(self, res, pub_date, site_url):
        row = []
        res_url = site_url + res.absolute_url
        funding_agencies = res.metadata.funding_agencies.all()
        row.append(res_url if res_url else None)
        row.append(res.doi if res.doi else None)
        title = res.metadata.title.value
        row.append(title if title else None)
        row.append(res.resource_type if res.resource_type else None)
        row.append(pub_date if pub_date else None)

        if funding_agencies:
            num_funders = len(funding_agencies)
            if num_funders > self.max_funders:
                self.max_funders = num_funders
            for f in funding_agencies:
                row.append(f.agency_name if f.agency_name else None)
                row.append(f.agency_url if f.agency_url else None)
                row.append(f.award_title if f.award_title else None)
                row.append(f.award_number if f.award_number else None)
        self.rows.append(row)

    def write_csv(self):
        # write headers last since funders is variable number
        headers = ['url', 'doi', 'title', 'type', 'pub_date']
        for i in range(1, self.max_funders + 1):
            headers.append(f"agency_name_{i}")
            headers.append(f"agency_url_{i}")
            headers.append(f"award_title_{i}")
            headers.append(f"award_number_{i}")

        # insert the headers
        self.writer.writerow(headers)

        for row in self.rows:
            self.writer.writerow(row)
        self.csvfile.close()
