from django.conf.urls import patterns, url
import views

urlpatterns = patterns(
    '', url(r'^_internal/(?P<resource_id>[0-9a-f]+)/(?P<coverage_type>[A-z]+)/update-coverage/$',
            views.update_resource_coverage,
            name="update_resource_coverage")
)
