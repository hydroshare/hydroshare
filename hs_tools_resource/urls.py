from django.conf.urls import patterns, url
from hs_tools_resource import views

urlpatterns = patterns('',
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<user>[A-z0-9]+)/(?P<tooltype>[A-z0-9]+)/go-for-tools/$', views.go_for_tools),
    )