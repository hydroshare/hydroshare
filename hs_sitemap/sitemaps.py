from django.contrib import sitemaps
from django.urls import reverse
from hs_core.models import BaseResource
from hs_access_control.models import Community
from django.contrib.auth.models import Group
from django.db.models import Q


class PagesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return ['home', 'login', 'apps']

    def location(self, item):
        return reverse(item)


class CommunitiesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'weekly'

    def items(self):
        return Community.objects.filter(active=True)

    def location(self, item):
        return f'/community/{item.id}'


class GroupsSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return Group.objects.filter(gaccess__active=True)

    def location(self, item):
        return f'/group/{item.id}'


class ResourcesSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'hourly'

    def items(self):
        return BaseResource.objects.filter(Q(raccess__public=True) | Q(raccess__discoverable=True))

    def location(self, item):
        return item.absolute_url

    def lastmod(self, item):
        return item.last_updated
