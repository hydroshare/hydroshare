# coding=utf-8
from django.conf.urls import url
from hs_file_types import views

urlpatterns = [
    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<file_id>[0-9]+)/'
        r'(?P<hs_file_type>[A-z]+)/set-file-type/$',
        views.set_file_type,
        name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<hs_file_type>[A-z]+)/set-file-type/$',
        views.set_file_type,
        name="set_file_type"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/remove-aggregation/$',
        views.remove_aggregation,
        name="remove_aggregation"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/delete-aggregation/$',
        views.delete_aggregation,
        name="delete_aggregation"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/move-aggregation/(?P<tgt_path>.+)$',
        views.move_aggregation,
        name="move_aggregation"),

    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/'
        r'(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/move-aggregation/$',
        views.move_aggregation,
        name="move_aggregation"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<element_name>[A-z]+)/'
        r'(?P<element_id>[0-9]+)/update-file-metadata/$',
        views.update_metadata_element,
        name="update_file_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/(?P<element_name>[A-z]+)/'
        r'add-file-metadata/$',
        views.add_metadata_element,
        name="add_file_metadata"),

    url(r'^_internal/(?P<hs_file_type>[A-z]+)/(?P<file_type_id>[0-9]+)/coverage/'
        r'(?P<element_id>[0-9]+)/delete-file-coverage/$',
        views.delete_coverage_element,
        name="delete_file_coverage"),

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

    url(r'^_internal/(?P<file_type_id>[0-9]+)/(?P<coverage_type>[A-z]+)/'
        r'update-coverage-fileset/$',
        views.update_aggregation_coverage,
        name="update_fileset_coverage"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-reftimeseries-abstract/$',
        views.update_refts_abstract,
        name="update_reftimeseries_abstract"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-timeseries-abstract/$',
        views.update_timeseries_abstract,
        name="update_timeseries_abstract"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-modelprogram-metadata/$',
        views.update_model_program_metadata,
        name="update_modelprogram_metadata"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-modelinstance-metadata/$',
        views.update_model_instance_metadata,
        name="update_modelinstance_metadata"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-modelinstance-metadata-json/$',
        views.update_model_instance_metadata_json,
        name="update_modelinstance_metadata_json"),

    url(r'^_internal/(?P<file_type_id>[0-9]+)/'
        r'update-modelinstance-meta-schema/$',
        views.update_model_instance_meta_schema,
        name="update_modelinstance_meta_schema"),

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
]
