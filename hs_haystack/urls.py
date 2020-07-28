from hs_haystack.views import HaystackView
from django.conf.urls import url

urlpatterns = [
    url(r'^/search/?$', HaystackView.as_view(), name='haystack_view'),
]
