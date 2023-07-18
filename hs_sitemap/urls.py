from django.conf.urls import url

from django.contrib.sitemaps import views

from .sitemaps import PagesSitemap, ResourcesSitemap

sitemaps = {
    "resources": ResourcesSitemap,
    "pages": PagesSitemap
}
sitemap_view = 'django.contrib.sitemaps.views.sitemap'


urlpatterns = [
    url(r'^\.xml$', views.index, {'sitemaps': sitemaps}),
    url(r'^-(?P<section>.+)\.xml$', views.sitemap, {'sitemaps': sitemaps}, name=sitemap_view),
]
