__author__ = 'Hong Yi'
import django.dispatch

pre_create_resource = django.dispatch.Signal(providing_args=['metadata', 'files'])
post_create_resource = django.dispatch.Signal(providing_args=['resource', 'metadata'])

pre_add_files_to_resource = django.dispatch.Signal(providing_args=['files', 'resource'])
pre_delete_file_from_resource = django.dispatch.Signal(providing_args=['file', 'resource'])
post_add_files_to_resource = django.dispatch.Signal(providing_args=['files', 'resource'])

pre_metadata_element_create = django.dispatch.Signal(providing_args=['element_name', 'request'])
pre_metadata_element_update = django.dispatch.Signal(providing_args=['element_name', 'element_id' 'request'])