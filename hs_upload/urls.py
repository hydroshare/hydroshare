from django.conf.urls import url

from hs_upload.views import UploadContextView, event

urlpatterns = [
    # for upload setup request from resource landing page
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(),
        name='upload_context'),
    url(r'^event/(?P<path>.*)$', event, name='upload_event'),
]
