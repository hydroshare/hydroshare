from django.conf.urls import patterns, url
from hs_labels import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/label-resource-action/$', views.resource_labeling_action),
    url(r'^_internal/label-resource-action/$', views.resource_labeling_action),
    )