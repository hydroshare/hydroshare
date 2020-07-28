from hs_haystack import HaystackView
from django.conf.urls import url

urlpatterns = [
    url(r'^/search/?$', HaystackView.as_view(), name='haystack_view'),
]
