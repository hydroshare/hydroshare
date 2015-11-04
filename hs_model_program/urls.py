__author__ = 'tonycastronova'

from django.conf.urls import patterns, url

from hs_model_program import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = patterns('',
    url(r'^_internal/get-model-metadata/$', views.get_model_metadata),
    url(r'^_internal/get-model-metadata-files/$', views.get_model_metadata_files),
    )
urlpatterns += staticfiles_urlpatterns()