# coding=utf-8
from django.conf.urls import patterns, url
from hs_file_types import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<resource_id>[A-z0-9]+)/(?P<file_id>[0-9]+)/'
        r'(?P<hs_file_type>[A-z]+)/extract-file-metadata/$',
        views.extract_metadata,
        name="extract_file_metadata"),

    )