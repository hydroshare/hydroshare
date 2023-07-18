from django.contrib import sitemaps
from django.urls import reverse
from hs_core.models import BaseResource
from django.db.models import Q


class PagesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'login', 'apps']

    def location(self, item):
        return reverse(item)


class ResourcesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return BaseResource.objects.filter(Q(raccess__public=True) | Q(raccess__discoverable=True))

    def location(self, item):
        return item.get_absolute_url()

    def lastmod(self, item):
        return item.last_updated
