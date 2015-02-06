__author__ = 'Hong Yi'
import django.dispatch

# TODO: remove 'dublin_metadata' from the list of providing_args
pre_create_resource = django.dispatch.Signal(providing_args=['dublin_metadata', 'metadata', 'files'])
post_create_resource = django.dispatch.Signal(providing_args=['resource', 'metadata'])

pre_metadata_element_create = django.dispatch.Signal(providing_args=['element_name', 'request'])
pre_metadata_element_update = django.dispatch.Signal(providing_args=['element_name', 'element_id' 'request'])