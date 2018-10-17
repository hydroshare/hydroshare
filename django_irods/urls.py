from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',
    # for download request from resource landing page
    url(r'^download/(?P<path>.*)$', 'django_irods.views.download'),
    # for download request from REST API
    url(r'^rest_download/(?P<path>.*)$', 'django_irods.views.rest_download',
        name='rest_download'),
    # for AJAX poll from resource landing page
    url(r'^check_task_status/$', 'django_irods.views.check_task_status'),
    # for REST API poll
    url(r'^rest_check_task_status/(?P<task_id>[A-z0-9\-]+)$',
        'django_irods.views.rest_check_task_status',
        name='rest_check_task_status'),
)
