"""This prints all variable names matching a specific prefix

* By default, prints errors on stdout.
"""

from django.core.management.base import BaseCommand
from hs_odm2.models import ODM2Variable


class Command(BaseCommand):
    help = "query ODM2 variable name database for all entries."

    def handle(self, *args, **options):
        print(list(ODM2Variable.all()))
