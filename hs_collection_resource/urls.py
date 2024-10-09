from django.urls import re_path

from hs_collection_resource import views

urlpatterns = [
    re_path(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection/$', views.update_collection),
    re_path(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection-for-deleted-resources/$',
            views.update_collection_for_deleted_resources),
    re_path(r'^_internal/calculate-collection-coverages/(?P<shortkey>[A-z0-9]+)/$',
            views.calculate_collection_coverages, name='calculate-collection-coverages'),
    re_path(r'^_internal/(?P<shortkey>[A-z0-9]+)/get-collectable-resources/$',
            views.get_collectable_resources_modal, name='get-collectable-resources'),
]
