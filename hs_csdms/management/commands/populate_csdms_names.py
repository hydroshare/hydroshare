"""This populates the CSMDS database based upon the CSDMS file

* By default, prints errors on stdout.
"""

from django.core.management.base import BaseCommand
from hs_csdms.models import CSDMSName


class Command(BaseCommand):
    help = "populate CSDMSName database with external file."

    def handle(self, *args, **options):
        CSDMSName.clear()
        CSDMSName.populate_csdms_names()
