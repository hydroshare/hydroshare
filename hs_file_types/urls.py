# coding=utf-8
from django.conf.urls import patterns, url
from hs_file_types import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<resource_id>[A-z0-9]+)/(?P<file_id>[0-9]+)/'
        r'(?P<hs_file_type>[A-z]+)/set-file-type/$',
        views.set_file_type,
        name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[A-z0-9]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/delete-file-type/$',
        views.delete_file_type,
        name="delete_file_type"),

    )