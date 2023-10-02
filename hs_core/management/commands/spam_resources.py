# -*- coding: utf-8 -*-

"""
Show resources that contain spam patterns
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core import hydroshare
from django.db.models import F
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = "Show resources that contain spam patterns."

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, dest='days', help='include resources updated in the last X days')
        # Named (optional) arguments
        parser.add_argument(
            '--published',
            action='store_true',  # True for presence, False for absence
            dest='published',  # value is options['published']
            help='filter to just published resources',
        )
        parser.add_argument(
            '--discoverable',
            action='store_true',  # True for presence, False for absence
            dest='discoverable',  # value is options['published']
            help='filter to just discoverable resources',
        )

    def handle(self, *args, **options):
        resources = BaseResource.objects.all()
        days = options['days']
        published = options['published']
        discoverable = options['discoverable']
        site_url = hydroshare.utils.current_site_url()
        if discoverable:
            print("FILTERING TO INCLUDE DISCOVERABLE RESOURCES")
            resources = resources.filter(raccess__discoverable=True)
        if published:
            print("FILTERING TO INCLUDE PUBLISHED RESOURCES")
            resources = resources.filter(raccess__published=True)

        if days:
            print(f"FILTERING TO INCLUDE RESOURCES UPDATED IN LAST {days} DAYS")
            cuttoff_time = timezone.now() - timedelta(days)
            resources = resources.filter(updated__gte=cuttoff_time)

        if not resources:
            print("NO RESOURCES FOUND MATCHING YOUR FILTER ARGUMENTS")
            return

        resources = resources.order_by(F('updated').asc(nulls_first=True))

        total_res_to_check = resources.count()
        current_resource = 0
        shadow_banned_resources = []
        allowlisted = []
        for resource in resources.iterator():
            current_resource += 1
            res_url = site_url + resource.absolute_url
            print(f"{current_resource}/{total_res_to_check}: Checking resource {res_url}")
            if not resource.free_of_spam_patterns:
                print("Resource contains spam pattern")
                if resource.spam_allowlisted:
                    allowlisted.append(res_url)
                    print("== THIS RESOURCE HAS BEEN ALLOWLISTED AND WILL SHOW UP IN DISCOVER ==")
                else:
                    shadow_banned_resources.append(res_url)
                print(f"Resources thus far with spam patterns: {len(shadow_banned_resources)}")
        print("*" * 100)

        if shadow_banned_resources:
            print(f"List of {len(shadow_banned_resources)} resources containing spam patterns:")
            for res in shadow_banned_resources:
                print(res)
            print("*" * 100)

        if allowlisted:
            print(f"List of {len(allowlisted)} resources that have been allowlisted:")
            for res in allowlisted:
                print(res)

        print("Complete.")
