from django.urls import re_path

from hs_core import views

urlpatterns = [
    # URLs to resolve hydroshare file urls that are part of the resourcemap xml document
    re_path(
        r"^resource/(?P<shortkey>[A-z0-9]+)/data/contents/(?P<filepath>.*)/$",
        views.file_download_url_mapper,
        name="get_resource_file",
    ),
    re_path(
        r"^resource/(?P<shortkey>[A-z0-9]+)/data/(?P<filepath>[^/]+)/$",
        views.file_download_url_mapper,
        name="get_resourcemap_or_metadata_file",
    ),
    re_path(
        r"^resource/(?P<shortkey>[A-z0-9]+)/(?P<filepath>[^/]+)/$",
        views.file_download_url_mapper,
        name="get_a_bagit_file",
    ),
]
