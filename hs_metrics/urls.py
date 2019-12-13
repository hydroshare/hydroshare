from django.conf.urls import url
from hs_metrics import views

urlpatterns = [
    # users API

    url(r'^metrics/$', views.HydroshareSiteMetrics.as_view()),

]

