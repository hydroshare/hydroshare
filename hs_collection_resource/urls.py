from django.conf.urls import url
from hs_collection_resource import views

urlpatterns = [
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection/$', views.update_collection),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection-for-deleted-resources/$',
        views.update_collection_for_deleted_resources),
    url(r'^_internal/calculate-collection-coverages/(?P<shortkey>[A-z0-9]+)/$',
        views.calculate_collection_coverages, name='calculate-collection-coverages'),
]