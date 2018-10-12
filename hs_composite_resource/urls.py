from django.conf.urls import url
from views import update_resource_coverage

urlpatterns = [
    url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<coverage_type>[A-z]+)/update-coverage/$',
        update_resource_coverage, name="update_resource_coverage")
]
