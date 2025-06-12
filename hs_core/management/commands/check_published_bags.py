"""
Check for published resources and create bags if necessary.
"""
from django.core.management.base import BaseCommand
from hs_core.tasks import ensure_published_resources_have_bags


class Command(BaseCommand):
    help = "Check for published resources and create bags if necessary."

    def handle(self, *args, **options):
        ensure_published_resources_have_bags()
