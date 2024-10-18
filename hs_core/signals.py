import django.dispatch

pre_create_resource = django.dispatch.Signal()
post_create_resource = django.dispatch.Signal()

pre_add_files_to_resource = django.dispatch.Signal()
pre_delete_file_from_resource = django.dispatch.Signal()
post_delete_file_from_resource = django.dispatch.Signal()

pre_metadata_element_create = django.dispatch.Signal()
pre_metadata_element_update = django.dispatch.Signal()
post_metadata_element_update = django.dispatch.Signal()

pre_download_file = django.dispatch.Signal()
pre_download_resource = django.dispatch.Signal()

pre_check_bag_flag = django.dispatch.Signal()

pre_delete_resource = django.dispatch.Signal()
pre_move_or_rename_file_or_folder = django.dispatch.Signal()

post_remove_file_aggregation = django.dispatch.Signal()
post_add_generic_aggregation = django.dispatch.Signal()
post_add_geofeature_aggregation = django.dispatch.Signal()
post_add_netcdf_aggregation = django.dispatch.Signal()
post_add_raster_aggregation = django.dispatch.Signal()
post_add_reftimeseries_aggregation = django.dispatch.Signal()
post_add_timeseries_aggregation = django.dispatch.Signal()
post_raccess_change = django.dispatch.Signal()
post_spam_whitelist_change = django.dispatch.Signal()
