import django.dispatch

pre_create_resource = django.dispatch.Signal(providing_args=['metadata', 'files'])
post_create_resource = django.dispatch.Signal(providing_args=['sender', 'resource', 'user', 'metadata','validate_files'])

pre_add_files_to_resource = django.dispatch.Signal(providing_args=['files', 'resource'])
pre_delete_file_from_resource = django.dispatch.Signal(providing_args=['file', 'resource'])
post_delete_file_from_resource = django.dispatch.Signal(providing_args=['resource'])
post_add_files_to_resource = django.dispatch.Signal(providing_args=['files', 'resource'])

pre_metadata_element_create = django.dispatch.Signal(providing_args=['element_name', 'request'])
pre_metadata_element_update = django.dispatch.Signal(providing_args=['element_name', 'element_id',
                                                                     'request'])
post_metadata_element_update = django.dispatch.Signal(providing_args=['element_name', 'element_id'])

pre_download_file = django.dispatch.Signal(providing_args=['sender','request','resource', 'download_file_name'])

pre_check_bag_flag = django.dispatch.Signal(providing_args=['resource'])

post_delete_resource = django.dispatch.Signal(providing_args=['request', 'user', 'shortkey',
                                                              'resource', 'resource_title', 'resource_type'])

pre_move_or_rename_file_or_folder = django.dispatch.Signal(providing_args=['resource',
                                                                           'src_full_path',
                                                                           'tgt_full_path'])

post_remove_file_aggregation = django.dispatch.Signal(providing_args=['resource', 'files'])
post_add_generic_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_add_geofeature_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_add_netcdf_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_add_raster_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_add_reftimeseries_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_add_timeseries_aggregation = django.dispatch.Signal(providing_args=['resource', 'file'])
post_raccess_change = django.dispatch.Signal(providing_args=['resource'])
