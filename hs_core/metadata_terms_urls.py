
from django.conf.urls import url
from hs_core import views

# URLs to resolve hydroshare metadata terms urls that are part of the science metadata xml document

urlpatterns = [url(r'^terms/$', views.get_metadata_terms_page, name='get_metadata_terms_page'),
                       url(r'^terms/([A-z]*)/$', views.get_metadata_terms_page, name='get_metadata_terms_page'),
]