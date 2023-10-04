"""Lists all the resources published in a given year.
"""

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

    def handle(self, *args, **options):
        days = options['days']
        resources = BaseResource.objects.filter(raccess__published=True)
        owner = options['owned_by']
        res_type = options['type']

        if owner is not None:
            try:
                owner = User.objects.get(username=owner)
                resources.filter(r2urp__user=owner,
                                 r2urp__privilege=PrivilegeCodes.OWNER)
            except ObjectDoesNotExist:
                print(f"User matching {owner} not found")

        if res_type is not None:
            if res_type in ["CompositeResource", "CollectionResource"]:
                resources.filter(resource_type=res_type)
            else:
                print(f"Type {res_type} is not supported. Must be 'CompositeResource' or 'CollectionResource'")

        resources = resources.order_by(F('updated').asc(nulls_first=True))

        for resource in resources:
            pub_date = self.get_publication_date(resource)
            if options['year']:
                if pub_date.year != int(options['year']):
                    continue
            if days:
                cuttoff_time = timezone.now() - timedelta(days)
                if not pub_date >= cuttoff_time:
                    continue
            self.print_resource(resource, pub_date)

    def get_publication_date(self, resource):
        published_date = resource.metadata.dates.filter(type="published").first()
        if not published_date:
            print(f"Publication date not found for {resource.short_id}")
        return published_date.start_date

    def print_resource(self, res, pub_date):
        site_url = hydroshare.utils.current_site_url()
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
