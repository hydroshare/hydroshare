__author__ = 'tonycastronova'

from django.conf.urls import patterns, url

from hs_model_program import views

urlpatterns = patterns('',
    url(r'^_internal/get-model-metadata/$', views.get_model_metadata),
    )