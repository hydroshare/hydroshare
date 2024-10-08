from django.urls import re_path

from django_irods.views import download, rest_check_task_status, rest_download

urlpatterns = [
    # for download request from resource landing page
    re_path(r'^download/(?P<path>.*)$', download, name='django_irods_download'),
    # for download request from REST API
    re_path(r'^rest_download/(?P<path>.*)$', rest_download, name='rest_download'),
    # for REST API poll
    re_path(r'^rest_check_task_status/(?P<task_id>[A-z0-9\-]+)$',
            rest_check_task_status,
            name='rest_check_task_status'),
]
