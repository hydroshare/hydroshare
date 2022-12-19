"""This does a comprehensive test of the json-ld of a resource

This loops through a list of resources and checks the ld+json
metadata against the official Google Structured testing tool.

Please note this requires setting the GOOGLE_COOKIE_HASH
directive inside local_settings.py
"""

from django.core.management.base import BaseCommand
from hs_core.models import BaseResource
from hs_core.management.utils import CheckJSONLD


class Command(BaseCommand):
    help = "Checks all resources for ."

    def add_arguments(self, parser):

        # a list of resource id's: none does nothing.
        parser.add_argument("resource_ids", nargs="*", type=str)

        # Named (optional) arguments
        parser.add_argument(
            "--log",
            action="store_true",  # True for presence, False for absence
            dest="log",  # value is options['log']
            help="log errors to system log",
        )

    def handle(self, *args, **options):
        if len(options["resource_ids"]) > 0:  # an array of resource short_id to check.
            for rid in options["resource_ids"]:
                CheckJSONLD(rid).test()
        else:
            for r in BaseResource.objects.all():
                CheckJSONLD(r.short_id).test()
