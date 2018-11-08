from django.conf.urls import url
from hs_labels import views

urlpatterns = [
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/label-resource-action/$', views.resource_labeling_action),
    url(r'^_internal/label-resource-action/$', views.resource_labeling_action),
]