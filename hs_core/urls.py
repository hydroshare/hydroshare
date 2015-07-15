from django.conf.urls import patterns, url
from hs_core import views

#
# 'sinless' = EXCLUSIVELY uses the hydroshare module to update resource/persmission/etc state
#

urlpatterns = patterns('',

    # resource API

    # sinless
    url(r'^resourceTypes/$', views.resource_rest_api.ResourceTypes.as_view(),
        name='list_resource_types'),
    url(r'^resourceList/$', views.resource_rest_api.ResourceList.as_view(),
        name='list_resources'),
    url(r'^resource/$', views.resource_rest_api.ResourceCreate.as_view(),
        name='create_resource'),
    url(r'^resource/(?P<pk>[A-z0-9]+)/$', views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),

    # SINFUL! directly manipulates `res.public`
    # changes needed: mirror updates to HSAccess
    url(r'^resource/accessRules/(?P<pk>[A-z0-9]+)/$', views.resource_rest_api.AccessRulesUpdate.as_view(),
        name='update_access_rules'),

    # sinless
    url(r'^sysmeta/(?P<pk>[A-z0-9]+)/$', views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_system_metadata'),
    url(r'^scimeta/(?P<pk>[A-z0-9]+)/$', views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='get_update_science_metadata'),
    url(r'^resource/(?P<pk>[A-z0-9]+)/files/$', views.resource_rest_api.ResourceFileCRUD.as_view(),
        name='add_resource_file'),
    url(r'^resource/(?P<pk>[A-z0-9]+)/files/(?P<filename>[^/]+)/$',
        views.resource_rest_api.ResourceFileCRUD.as_view(), name='get_update_delete_resource_file'),

    # internal API

    # sinless
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-file-to-resource/$', views.add_file_to_resource),

    # **** directly manipulates metadata, but thats probably OK by HSAccess
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/add-metadata/$', views.add_metadata_element),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/update-metadata/$', views.update_metadata_element),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/delete-metadata/$', views.delete_metadata_element),

    # sinless
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource-file/(?P<f>[0-9]+)/$', views.delete_file),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource/$', views.delete_resource),

    # **** SINFUL!
    # changes needed: mirror updates to HSAcccess
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/change-permissions/$', views.change_permissions),

    # N/A
    url(r'^_internal/verify_captcha/$', views.verify_captcha),

    # **** SINFUL! directly manipulates res.public
    # changes needed: mirror updates to HSAccess
    url(r'^_internal/publish/$', views.publish),

    # sinless
    url(r'^_internal/create-resource/$', views.create_resource_select_resource_type),
    url(r'^_internal/create-resource/do/$', views.create_resource),
    url(r'^_internal/verify-account/$', views.verify_account),
    url(r'^_internal/resend_verification_email/$', views.resend_verification_email),
    url(r'^_internal/(?P<resource_type>[A-z]+)/supported-file-types/$', views.get_supported_file_types_for_resource_type),
    url(r'^_internal/(?P<resource_type>[A-z]+)/allow-multiple-file/$', views.is_multiple_file_allowed_for_resource_type),
    url(r'^_internal/search/autocomplete/', "hs_core.views.autocomplete.autocomplete"),
)

