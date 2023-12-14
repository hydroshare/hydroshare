"""Extra URLs that add debugging capabilities to resources."""

from django.conf.urls import url
from hs_core import views

urlpatterns = [
    # Resource Debugging: print consistency problems in a resource
    url(r'^debug/resource/(?P<shortkey>[0-9a-f-]+)/$',
        views.debug_resource_view.debug_resource,
        name='debug_resource'),
    url(r'^debug/resource/(?P<shortkey>[0-9a-f-]+)/irods-issues/$',
        views.debug_resource_view.irods_issues,
        name='debug_resource'),
    url(r'^debug/resource/(?P<shortkey>[0-9a-f-]+)/non-preferred-paths/$',
        views.debug_resource_view.check_for_non_preferred_paths,
        name='debug_resource'),

    url(r'^taskstatus/(?P<task_id>[A-z0-9\-]+)/$',
        views.debug_resource_view.check_task_status,
        name='get_debug_task_status'),
    url(r'^taskstatus/path-check-task/(?P<task_id>[A-z0-9\-]+)/$',
        views.debug_resource_view.check_non_preferred_paths_task_status,
        name='get_path_check_task_status'),
]
