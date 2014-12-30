from django.conf.urls import patterns, url
from resource_aggregation import views

urlpatterns = patterns('',
    url(r'^_internal/create-resource-aggregation/$', views.create_resource_aggregation),
    url(r'^resource/(?P<shortkey>[A-z0-9]+)/add-resource/$', views.add_resource_view),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-resource/$', views.add_resource),
    )
