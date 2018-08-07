from django.conf.urls import patterns, url
from hs_core import views
from django.conf import settings

urlpatterns = patterns('',

    # URLs to resolve hydroshare file urls that are part of the resourcemap xml document
    url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/contents/(.*)/$', views.file_download_url_mapper,
        name='get_resource_file'),

    url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/([^/]+)/$', views.file_download_url_mapper,
        name='get_resourcemap_or_metadata_file'),

    # URLs related to file downloading 
    url(r'^zips/[^/]+/[^/]+/(?P<shortkey>[A-z0-9]+)/(.*)$', views.file_download_url_mapper, 
        name='get_stored_zipfile'), 

    url(r'^bags/(?P<shortkey>[A-z0-9]+).zip$', views.file_download_url_mapper, 
        name='get_zipped_bag'),
)
