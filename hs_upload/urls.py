from django.conf.urls import url

from hs_upload.views import UploadContextView, UploaderView, start, finish

urlpatterns = [
    # Set up a separate upload page that manages an upload.
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(), name='upload_context'),

    # Set up a subpage that uploads a specific file; file is passed via window.object
    url(r'^_uploader/(?P<path>.*)$', UploaderView.as_view(), name='uploader'),

    # Start and authorize an upload
    url(r'^start/(?P<path>.*)$', start, name='upload_start'),

    # Finish and commit an upload
    url(r'^finish/(?P<path>.*)$', finish, name='upload_finish'),
]
