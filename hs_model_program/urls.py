
from django.conf.urls import url

from hs_model_program import views

urlpatterns = [
    url(r'^_internal/get-model-metadata/$', views.get_model_metadata),
]