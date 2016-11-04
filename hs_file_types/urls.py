# coding=utf-8
from django.conf.urls import patterns, url
from hs_file_types import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<resource_id>[0-9a-f-]+)/(?P<file_id>[0-9]+)/'
        r'(?P<hs_file_type>[A-z]+)/set-file-type/$',
        views.set_file_type,
        name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f-]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/delete-file-type/$',
        views.delete_file_type,
        name="delete_file_type"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<element_name>[A-z]+)/'
        r'(?P<element_id>[0-9]+)/update-file-metadata/$',
        views.update_metadata_element,
        name="update_file_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<metadata_mode>[a-z]+)/'
        r'get-file-metadata/$', views.get_metadata, name="get_file_metadata"),
    )