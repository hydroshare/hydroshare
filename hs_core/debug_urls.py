"""Extra URLs that add debugging capabilities to resources."""

from django.urls import re_path

from hs_core import views

urlpatterns = [
    # Resource Debugging: print consistency problems in a resource
    re_path(
        r"^debug/resource/(?P<shortkey>[0-9a-f-]+)/$",
        views.debug_resource_view.debug_resource,
        name="debug_resource",
    ),
    re_path(
        r"^debug/resource/(?P<shortkey>[0-9a-f-]+)/s3-issues/$",
        views.debug_resource_view.s3_issues,
        name="debug_resource",
    ),
    re_path(
        r"^debug/resource/(?P<shortkey>[0-9a-f-]+)/non-preferred-paths/$",
        views.debug_resource_view.check_for_non_preferred_paths,
        name="debug_resource",
    ),
    re_path(
        r"^taskstatus/(?P<task_id>[A-z0-9\-]+)/$",
        views.debug_resource_view.check_task_status,
        name="get_debug_task_status",
    ),
    re_path(
        r"^taskstatus/path-check-task/(?P<task_id>[A-z0-9\-]+)/$",
        views.debug_resource_view.check_non_preferred_paths_task_status,
        name="get_path_check_task_status",
    ),
]
