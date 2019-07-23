"""This synchronizes the ODM variable class with the external website.

* By default, prints errors on stdout.
"""

from django.core.management.base import BaseCommand
from hs_odm2.models import ODM2Variable


class Command(BaseCommand):
    help = "synchronize ODM2 variable database with external site."

    def handle(self, *args, **options):
        ODM2Variable.sync()
