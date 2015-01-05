__author__ = 'pabitra'

import django.dispatch

pre_metadata_element_create = django.dispatch.Signal(providing_args=['element_name', 'request'])
pre_metadata_element_update = django.dispatch.Signal(providing_args=['element_name', 'element_id' 'request'])