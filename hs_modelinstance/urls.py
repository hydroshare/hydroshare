from django.conf.urls import patterns, url

from hs_modelinstance import views

urlpatterns = patterns('',
    url(r'^_internal/is-executed-by/$', views.is_executed_by),
    )