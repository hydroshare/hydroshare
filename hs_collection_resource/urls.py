from django.conf.urls import patterns, url
from hs_collection_resource import views

urlpatterns = patterns(
    '',
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/update-collection/$', views.update_collection),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/collection-member-permission/(?P<user_id>[0-9]+)/$',
        views.collection_member_permission),
                      )
