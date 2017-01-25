from doc_schema import schema_view
from django.conf.urls import url
import hs_core

urlpatterns = [
    url(r'^$', schema_view),

    url(r'^resources/$',
        hs_core.views.resource_rest_api.ResourceListCreate.as_view(),
        name='list_create_resource'),

    url(r'^resources/(?P<pk>[0-9a-f-]+)/$',
        hs_core.views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),
]