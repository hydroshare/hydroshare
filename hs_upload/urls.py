from django.conf.urls import url

from hs_upload.views import UploadContextView, start, finish

urlpatterns = [
    # Set up a separate upload page that manages an upload.
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(), name='upload_context'),

    # Start and authorize an upload
    url(r'^start/(?P<path>.*)$', start, name='upload_start'),

    # Finish and commit an upload
    url(r'^finish/(?P<path>.*)$', finish, name='upload_finish'),
]
