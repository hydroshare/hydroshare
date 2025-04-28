"""
Truncate Tracking tables to the last 60 days.
"""
from django.core.management.base import BaseCommand
from hs_tracking.models import Variable
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = "Truncate Variable tracking to the last 60 (default) days"

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, dest='days', default=60,
                            help='number of days to list')

    def handle(self, *args, **options):
        days = options['days']
        time_threshold = timezone.now() - timedelta(days=days)
        Variable.objects.filter(timestamp__lt=time_threshold).delete()
