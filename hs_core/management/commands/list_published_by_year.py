"""This lists all the resources published in a given year.

* By default, prints errors on stdout.
* Optional argument --log: logs output to system log.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from django.db.models import F
from datetime import timedelta
from django.utils import timezone


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
        count = 1
        resources = BaseResource.objects.filter(raccess__published=True)

        if options['owned_by'] is not None:
            owner = User.objects.get(username=options['owned_by'])
            resources.filter(r2urp__user=owner,
                             r2urp__privilege=PrivilegeCodes.OWNER)

        if options['type'] is not None:
            resources.filter(resource_type=options['type'])

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
            print("*" * 100)
            print(f"{count}/{resources.count()}")
            self.print_resource(resource, pub_date)
            count += 1

    def get_publication_date(self, resource):
        meta_dates = resource.metadata.dates.all()
        published_date = [dt for dt in meta_dates if dt.type == "published"]
        citation_date = None
        if published_date:
            citation_date = published_date[0]
        else:
            print(f"Publication date not found for {resource.short_id}")

        return citation_date.start_date

    def print_resource(self, res, pub_date):
        site_url = hydroshare.utils.current_site_url()
        res_url = site_url + res.absolute_url
        funding_agencies = res.metadata.funding_agencies.all()
        print(f"{res_url}")
        print(res.metadata.title.value)
        if pub_date:
            print(f"Published on {pub_date}")
        else:
            print("Resource has no publication date")

        if funding_agencies:
            print("Funding agency/agencies:")
            for f in funding_agencies:
                print(f.agency_name)
        else:
            print("Resource has no funding agency")

        if res.doi:
            print(res.doi)
        else:
            print("Resource has no doi")
