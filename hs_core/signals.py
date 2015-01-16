__author__ = 'Hong Yi'
import django.dispatch
pre_describe_resource = django.dispatch.Signal(providing_args=['files'])
pre_call_create_resource = django.dispatch.Signal(providing_args=['request_post'])

pre_create_resource = django.dispatch.Signal(providing_args=['dublin_metadata', 'metadata', 'files'])
post_create_resource = django.dispatch.Signal(providing_args=['resource', 'metadata'])