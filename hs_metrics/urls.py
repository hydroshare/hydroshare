from django.conf.urls import patterns, url
from hs_metrics import views

urlpatterns = patterns('',

    # users API

    url(r'^metrics/$', views.xDCIShareSiteMetrics.as_view()),

)

