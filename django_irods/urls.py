from django.conf.urls import patterns, url

urlpatterns = patterns('',

    # users API

    url(r'^download/$', 'django_irods.views.download'),
    url(r'^list/$', 'django_irods.views.list'),
)