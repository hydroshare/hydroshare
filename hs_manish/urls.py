from django.conf.urls import url
from hs_manish import views

urlpatterns = [
    url("/", views.index, name = "index"),
    url("/resource_landing", views.resource_landing, name="resource_landing"),
    url("/dashboard", views.dashboard, name="dashboard")
    ]