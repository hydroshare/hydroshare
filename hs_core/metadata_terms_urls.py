from django.urls import path, re_path

from hs_core import views

# URLs to resolve hydroshare metadata terms urls that are part of the science metadata xml document

urlpatterns = [
    path("terms/", views.get_metadata_terms_page, name="get_metadata_terms_page"),
    re_path(r"^terms/([A-z]*)/$", views.get_metadata_terms_page, name="get_metadata_terms_page"),
]
