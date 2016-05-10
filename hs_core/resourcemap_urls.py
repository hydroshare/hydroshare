__author__ = 'pabitra'
from django.conf.urls import patterns, url
from hs_core import views

urlpatterns = patterns('',

    # URLs to resolve hydroshare file urls that are part of the resourcemap xml document

     url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/(?P<filename>[^/]+)/$', views.file_download_url_mapper,
        name='get_resourcemap_or_metadata_file'),

     url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/contents/(?P<filename>[^/]+)/$', views.file_download_url_mapper,
        name='get_resource_file'),

     url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/contents/hydroshareuserZone/home/([A-z0-9]+)/(?P<filename>[^/]+)/$', views.file_download_url_mapper,
        name='get_resource_file'),
     )