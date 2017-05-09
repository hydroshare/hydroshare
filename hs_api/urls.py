from doc_schema import schema_view
from django.conf.urls import url
import hs_core

urlpatterns = [
    url(r'^$', schema_view),

    url(r'^resources/$',
        hs_core.views.resource_rest_api.ResourceListCreate.as_view(),
        name='list_create_resource'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/$',
        hs_core.views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/access/$',
        hs_core.views.resource_access_api.ResourceAccessUpdateDelete.as_view(),
        name='get_update_delete_resource_access'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/(?P<pathname>.+)/$',
        hs_core.views.resource_rest_api.ResourceFileCRUD.as_view(),
        name='get_update_delete_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/$',
        hs_core.views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='list_create_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/map/$',
        hs_core.views.resource_rest_api.ResourceMapRetrieve.as_view(),
        name='get_update_delete_resource_sysmeta'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/$',
        hs_core.views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='get_update_science_metadata'),

    # Resource metadata editing
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/elements/$',
        hs_core.views.resource_metadata_rest_api.MetadataElementsRetrieveUpdate.as_view(),
        name='get_update_science_metadata_elements'),

    # Update key-value metadata
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/custom/$',
        hs_core.views.update_key_value_metadata_public,
        name='update_custom_metadata'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/sysmeta/$',
        hs_core.views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_update_delete_resource_sysmeta'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/sysmeta/$',
        hs_core.views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_update_delete_resource_sysmeta'),
]