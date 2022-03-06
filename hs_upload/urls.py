from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from hs_upload.views import UploadContextView

urlpatterns = [
    # for upload setup request from resource landing page
    url(r'^context/(?P<path>.*)$', UploadContextView.as_view(),
        name='upload_context'),
]
