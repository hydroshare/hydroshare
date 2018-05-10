from django.conf.urls import url, patterns

from django.contrib.sitemaps import views
from mezzanine.core.sitemaps import DisplayableSitemap

from .sitemaps import PagesSitemap

sitemaps = {
    "resources": DisplayableSitemap,
    "pages": PagesSitemap
}
sitemap_view = 'django.contrib.sitemaps.views.sitemap'


urlpatterns = patterns(
    '',
    url(r'^\.xml$', views.index, {'sitemaps': sitemaps}),
    url(r'^-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps}, name=sitemap_view),
)
