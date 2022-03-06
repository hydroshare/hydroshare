from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from hs_upload.views import rest_upload, upload, UploadContextView

urlpatterns = [

    # for upload setup request from resource landing page
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(),
        name='upload_context'),

    # for upload proxy request from upload context page
    # can't authenticate due to packet requirements
    # TODO: use extension headers.  
    # url(r'^proxy/(?P<path>.*)$', csrf_exempt(upload), name='upload'),

    # for upload proxy request from REST API
    url(r'^rest_upload/(?P<path>.*)$', rest_upload, name='rest_upload')
]
