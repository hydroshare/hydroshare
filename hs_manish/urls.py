from django.conf.urls import url
from hs_manish import views

urlpatterns = [
    url("index", views.index, name = "index"),
    url("resource_landing", views.resource_landing, name="resource_landing"),
    url("dashboard", views.dashboard, name="dashboard"),
    url(r'^user_stats/(?P<username>[^\>]+)$', views.user_stats, name ="user_dashboard"),
    url("histogram", views.showHistogram, name="histogram"),
    ]
