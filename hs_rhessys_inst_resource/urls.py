from django.conf.urls import patterns

from hs_rhessys_inst_resource.views import RunModelView


urlpatterns = patterns('',
                       (r'(?P<resource_short_id>[A-z0-9]+)/runmodel/$', RunModelView.as_view()),
                       )
