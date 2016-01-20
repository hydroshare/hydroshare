from django.conf.urls import patterns, url
from hs_collection_resource import views

urlpatterns = patterns('',
    url(r'^_internal/update-collection/$', views.update_collection))