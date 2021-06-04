from django.conf.urls import include, url
from hs_community_mgmt import views

urlpatterns = [
    url(r'^cmgmt/$', views.TestView.as_view()),

]
