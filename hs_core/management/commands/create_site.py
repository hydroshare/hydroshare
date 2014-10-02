from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    Site.objects.get_or_create(
        domain='192.168.59.103:8000',
        name='default'
    )