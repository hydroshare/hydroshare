from django.conf.urls import patterns, url
from hs_core import views

urlpatterns = patterns('',

    # users API

    url(r'^resource/owner/(?P<pk>[A-z0-9]+)/$', views.users_api.SetResourceOwner.as_view()),
    url(r'^resource/accessRules/(?P<pk>[A-z0-9]+)/$', views.users_api.SetAccessRules.as_view()),
    url(r'^accounts/$', views.users_api.CreateOrListAccounts.as_view()),
    url(r'^accounts/(?P<pk>[A-z0-9]+)/$', views.users_api.UpdateAccountOrUserInfo.as_view()),
    url(r'^groups/$', views.users_api.CreateOrListGroups.as_view()),
    url(r'^groups/(?P<pk>[A-z0-9]+)/$', views.users_api.ListGroupMembers.as_view()),
    url(r'^groups/(?P<g>[A-z0-9]+)/owner/(?P<u>[A-z0-9]+)/$', views.users_api.SetOrDeleteGroupOwner.as_view()),
    url(r'^resources/$', views.users_api.GetResourceList.as_view()),

    # resource API

    url(r'^resource/$', views.resource_api.ResourceCRUD.as_view()),
    url(r'^resource/(?P<pk>[A-z0-9]+)/$', views.resource_api.ResourceCRUD.as_view()),
    url(r'^resource/(?P<pk>[A-z0-9]+)/files/$', views.resource_api.ResourceFileCRUD.as_view()),
    url(r'^resource/(?P<pk>[A-z0-9]+)/files/(?P<filename>[^/]+)/$', views.resource_api.ResourceFileCRUD.as_view()),
    url(r'^scimeta/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetUpdateScienceMetadata.as_view()),
    url(r'^sysmeta/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetUpdateSystemMetadata.as_view()),
    url(r'^capabilities/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetCapabilities.as_view()),
    url(r'^revisions/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetRevisions.as_view()),
    url(r'^related/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetRelated.as_view()), # raises not implemented
    url(r'^checksum/(?P<pk>[A-z0-9]+)/$', views.resource_api.GetChecksum.as_view()), # raises not implemented
    url(r'^publishResource/(?P<pk>[A-z0-9]+)/$', views.resource_api.PublishResource.as_view()), # raises not implemented
    url(r'^resolveDOI/(?P<doi>[A-z0-9]+)/$', views.resource_api.ResolveDOI.as_view()), # raises not implemented

    # internal API

    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-file-to-resource/$', views.add_file_to_resource),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-metadata/$', views.add_metadata_term),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-citation/$', views.add_citation),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource-file/(?P<f>[0-9]+)/$', views.delete_file),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource/$', views.delete_resource),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/change-permissions/$', views.change_permissions),
    url(r'^_internal/verify_captcha/$', views.verify_captcha),
    url(r'^_internal/publish/$', views.publish),
    url(r'^_internal/create-resource/$', views.create_resource),
    url(r'^_internal/resend_verification_email/$', views.resend_verification_email),
)

