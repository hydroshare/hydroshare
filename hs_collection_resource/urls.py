from django.conf.urls import patterns, url
from hs_collection_resource import views

urlpatterns = patterns(
    '',
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection/$', views.update_collection),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection-for-deleted-resources/$',
        views.update_collection_for_deleted_resources),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection-coverages/$',
        views.update_collection_coverages),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/calculate-collection-coverages/$',
        views.calculate_collection_coverages),
    )
