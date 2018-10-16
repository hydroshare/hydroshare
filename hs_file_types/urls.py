# coding=utf-8
from django.conf.urls import patterns, url
from hs_file_types import views

urlpatterns = patterns(
    '', url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<file_id>[0-9]+)/'
            r'(?P<hs_file_type>[A-z]+)/set-file-type/$',
            views.set_file_type,
            name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<hs_file_type>[A-z]+)/set-file-type/$',
        views.set_file_type,
        name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/delete-file-type/$',
        views.delete_file_type,
        name="delete_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/remove-aggregation/$',
        views.remove_aggregation,
        name="remove_aggregation"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<element_name>[A-z]+)/'
        r'(?P<element_id>[0-9]+)/update-file-metadata/$',
        views.update_metadata_element,
        name="update_file_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<element_name>[A-z]+)/'
        r'add-file-metadata/$',
        views.add_metadata_element,
        name="add_file_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/'
        r'update-file-keyvalue-metadata/$',
        views.update_key_value_metadata,
        name="update_file_keyvalue_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/'
        r'delete-file-keyvalue-metadata/$',
        views.delete_key_value_metadata,
        name="delete_file_keyvalue_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/'
        r'add-file-keyword-metadata/$',
        views.add_keyword_metadata,
        name="add_file_keyword_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/'
        r'delete-file-keyword-metadata/$',
        views.delete_keyword_metadata,
        name="delete_file_keyword_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/'
        r'update-filetype-dataset-name/$',
        views.update_dataset_name,
        name="update_filetype_datatset_name"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-reftimeseries-abstract/$',
        views.update_refts_abstract,
        name="update_reftimeseries_abstract"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-timeseries-abstract/$',
        views.update_timeseries_abstract,
        name="update_timeseries_abstract"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/update-netcdf-file/$',
        views.update_netcdf_file,
        name="update_netcdf_file"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/update-sqlite-file/$',
        views.update_sqlite_file,
        name="update_sqlite_file"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<metadata_mode>[a-z]+)/'
        r'get-file-metadata/$',
        views.get_metadata,
        name="get_file_metadata"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/(?P<series_id>[A-Za-z0-9-]+)/'
        r'(?P<resource_mode>[a-z]+)/'
        r'get-timeseries-file-metadata/$',
        views.get_timeseries_metadata,
        name="get_timeseries_file_metadata"),
    )
