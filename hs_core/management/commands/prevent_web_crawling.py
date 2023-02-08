# -*- coding: utf-8 -*-

"""
Prevent web-crawlers from indexing the site
"""

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from robots.models import Url, Rule


class Command(BaseCommand):
    help = "Prevent web-crawlers from indexing the site. This command is intended to be run after dev deployments."

    def add_arguments(self, parser):

        # a list of urls to disable
        parser.add_argument('disallowed_urls', nargs='*', type=str)

    def handle(self, *args, **options):
        # django-robots model definitions:
        # https://github.com/jazzband/django-robots/blob/5.0/src/robots/models.py
        r = Rule()
        r.robot = "*"
        r.crawl_delay = 5
        r.save()  # extra save here is necessary to do r.disallowed later
        r.sites.set(Site.objects.all())

        if len(options['disallowed_urls']) > 0:  # an array of urls to disable.
            for url in options['disallowed_urls']:
                try:
                    u = Url()
                    u.pattern = url
                    u.save()
                    r.disallowed.add(u)
                except Exception:
                    print(f"Disallow url: {url} failed.")
                    raise
        else:
            u = Url()
            u.pattern = "/"
            u.save()
            r.disallowed.add(u)
        r.save()
