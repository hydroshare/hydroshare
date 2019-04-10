"""Extra URLs that add debugging capabilities to resources."""

from django.conf.urls import url
from hs_core import views

urlpatterns = [
    # Resource Debugging: print consistency problems in a resource
    url(r'^resource/(?P<shortkey>[0-9a-f-]+)/debug/$',
        views.debug_resource_view.debug_resource,
        name='debug_resource'),
]
