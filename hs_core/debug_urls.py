from django.conf.urls import patterns, url
from hs_core import views

urlpatterns = patterns(
    '',
    # Resource Debugging: print consistency problems in a resource
    url(r'^resource/(?P<shortkey>[0-9a-f-]+)/debug/$',
        views.debug_resource_view.debug_resource,
        name='debug_resource'),
)
