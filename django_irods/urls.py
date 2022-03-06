from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from django_irods.views import rest_check_task_status,\
        rest_download, download,\
        rest_upload, upload,\
        UploadContextView

urlpatterns = [
    # for download request from resource landing page
    url(r'^download/(?P<path>.*)$', download, name='django_irods_download'),

    # for download request from REST API
    url(r'^rest_download/(?P<path>.*)$', rest_download, name='rest_download'),

    # for REST API poll
    url(r'^rest_check_task_status/(?P<task_id>[A-z0-9\-]+)$',
        rest_check_task_status,
        name='rest_check_task_status'),

    # # for upload setup request from resource landing page
    # url(r'^upload_context/(?P<path>.*)$', UploadContextView.as_view(),
    #     name='upload_context'),

    # # for upload proxy request from upload context page
    # # can't authenticate due to packet requirements
    # # TODO: use extension headers.  
    # # url(r'^upload/(?P<path>.*)$', csrf_exempt(upload), name='upload'),

    # # for upload proxy request from REST API
    # url(r'^rest_upload/(?P<path>.*)$', rest_upload, name='rest_upload')
]
