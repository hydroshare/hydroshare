# -*- coding: utf-8 -*-


from django.core.management.base import BaseCommand

from pprint import pprint

from django.conf import settings


class Command(BaseCommand):
    help = "Check synchronization between iRODS and Django."

    def handle(self, *args, **options):

        external = getattr(settings, 'EXTERNAL_CONFIG', None)
        pprint(external)
        if 'LINUX_ROOT' in external:
            root = external['LINUX_ROOT']
        else:
            root = '/tmp'
        print(root)
