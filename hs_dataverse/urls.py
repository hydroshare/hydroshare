from django.conf.urls import url
from . import views


urlpatterns = [url(r'^upload_dataset/$', views.upload_dataset, name='upload_dataset')]
