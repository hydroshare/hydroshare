from django.conf.urls import patterns, include, url
from ga_interactive.views import notebook_for_user

urlpatterns = patterns('',
    url(r'^notebook/(?P<path>.*)$', notebook_for_user),
)
