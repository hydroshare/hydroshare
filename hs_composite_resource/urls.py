from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<coverage_type>[A-z]+)/update-coverage/$',
            views.update_resource_coverage, name="update_resource_coverage"),
    re_path(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<coverage_type>[A-z]+)/delete-coverage/$',
            views.delete_resource_coverage, name="delete_resource_coverage"),
    re_path(r'^_internal/(?P<resource_id>[0-9a-f]+)/aggregation-files-to-sync/$',
            views.check_aggregation_files_to_sync, name="aggregation_files_to_sync"),
]
