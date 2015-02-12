from django.conf.urls import patterns, url

from hs_rhessys_inst_resource.views import RunModelView
from hs_rhessys_inst_resource.views import GetRunInfoJSON

urlpatterns = patterns('',
                       url(r'(?P<resource_short_id>[A-z0-9]+)/runmodel/$', RunModelView.as_view(),
                           name='hs_rhessys_inst_resource-runmodel'),
                       url(r'(?P<resource_short_id>[A-z0-9]+)/getruninfo(?:/(?P<token>[A-z0-9\-]+))?/$', 
                           GetRunInfoJSON.as_view(), # Note: token element is optional
                           name='hs_rhessys_inst_resource-getruninfo'),
                       )
