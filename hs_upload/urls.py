from django.conf.urls import url

from hs_upload.views import UploadContextView, start, finish

urlpatterns = [
    # for upload setup request from resource landing page
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(), name='upload_context'),
    url(r'^start/(?P<path>.*)$', start, name='upload_start'),
    url(r'^finish/(?P<path>.*)$', finish, name='upload_finish'),
]
