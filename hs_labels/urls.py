from django.urls import path, re_path

from hs_labels import views

urlpatterns = [
    re_path(r'^_internal/(?P<shortkey>[A-z0-9]+)/label-resource-action/$', views.resource_labeling_action),
    path('_internal/label-resource-action/', views.resource_labeling_action),
]
