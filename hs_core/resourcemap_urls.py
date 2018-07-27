from django.conf.urls import url
from hs_core import views

urlpatterns = [

    # URLs to resolve hydroshare file urls that are part of the resourcemap xml document

    url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/([^/]+)/$', views.file_download_url_mapper,
        name='get_resourcemap_or_metadata_file'),

    url(r'^resource/(?P<shortkey>[A-z0-9]+)/data/contents/(.*)/$', views.file_download_url_mapper,
        name='get_resource_file'),

]