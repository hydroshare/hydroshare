from django.conf.urls import url

from hs_upload.views import UploadContextView, UppyView, start, finish, stop

urlpatterns = [
    # using tus.io
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(), name='upload_context'),

    # using uppy
    url(r'^uppy/(?P<path>.*)$', UppyView.as_view(), name='uppy_context'),

    # Start and authorize an upload
    url(r'^start/(?P<path_of_folder>.*)$', start, name='upload_start'),

    # clean up and stop
    url(r'^stop/(?P<path_of_folder>.*)$', stop, name='upload_stop'),

    # Finish and commit an upload
    url(r'^finish/(?P<path_of_folder>.*)$', finish, name='upload_finish'),
]
