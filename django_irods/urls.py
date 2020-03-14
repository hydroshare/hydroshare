from django.conf.urls import url
from django_irods.views import rest_check_task_status, rest_download, download, check_task_status

urlpatterns = [
    # for download request from resource landing page
    url(r'^download/(?P<path>.*)$', download, name='django_irods_download'),
    # for download request from REST API
    url(r'^rest_download/(?P<path>.*)$', rest_download,
        name='rest_download'),
    # for AJAX poll from resource landing page
    url(r'^check_task_status/$', check_task_status),
    # for REST API poll
    url(r'^rest_check_task_status/(?P<task_id>[A-z0-9\-]+)$',
        rest_check_task_status,
        name='rest_check_task_status'),
]
