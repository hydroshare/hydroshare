"""
This calls all preparation routines involved in creating SOLR records.
It is used to debug SOLR harvesting. If any of these routines fails on
any resource, all harvesting ceases. This has caused many bugs.
"""

from django.core.management.base import BaseCommand
from hs_upload.models import Upload
from hs_upload.views import clear_all, print_all


class Command(BaseCommand):
    help = "clear tusd tables."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        print("All tusd operations in progress:")
        print_all()
        clear_all()
        print("All tusd state cleared.")
        
