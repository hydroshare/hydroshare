from django.contrib.sitemaps import views
from django.urls import re_path

from .sitemaps import (CommunitiesSitemap, GroupsSitemap, PagesSitemap,
                       ResourcesSitemap)

sitemaps = {
    "resources": ResourcesSitemap,
    "pages": PagesSitemap,
    "communities": CommunitiesSitemap,
    "groups": GroupsSitemap
}
sitemap_view = 'django.contrib.sitemaps.views.sitemap'


urlpatterns = [
    re_path(r'^\.xml$', views.index, {'sitemaps': sitemaps}),
    re_path(r'^-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps}, name=sitemap_view),
]
