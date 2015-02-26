from django.conf.urls import patterns, url
from hs_core import views

urlpatterns = patterns('',

    url(r'^resource/owner/(?P<pk>[A-z0-9]+)/$', views.users_api.SetResourceOwner.as_view()),
    url(r'^resource/accessRules/(?P<pk>[A-z0-9]+)/$', views.users_api.SetAccessRules.as_view()),
    url(r'^accounts/$', views.users_api.CreateOrListAccounts.as_view()),
    url(r'^accounts/(?P<pk>[A-z0-9]+)/$', views.users_api.UpdateAccountOrUserInfo.as_view()),
    url(r'^groups/$', views.users_api.CreateOrListGroups.as_view()),
    url(r'^groups/(?P<pk>[A-z0-9]+)/$', views.users_api.ListGroupMembers.as_view()),
    url(r'^groups/(?P<g>[A-z0-9]+)/owner/(?P<u>[A-z0-9]+)/$', views.users_api.SetOrDeleteGroupOwner.as_view()),
    url(r'^resources/$', views.users_api.GetResourceList.as_view()),

    # internal API

    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-file-to-resource/$', views.add_file_to_resource),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-metadata/$', views.add_metadata_term),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/add-metadata/$', views.add_metadata_element),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/update-metadata/$', views.update_metadata_element),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/delete-metadata/$', views.delete_metadata_element),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/add-citation/$', views.add_citation),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource-file/(?P<f>[0-9]+)/$', views.delete_file),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-resource/$', views.delete_resource),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/change-permissions/$', views.change_permissions),
    url(r'^_internal/verify_captcha/$', views.verify_captcha),
    url(r'^_internal/publish/$', views.publish),
    url(r'^_internal/create-resource/$', views.create_resource_select_resource_type),
    url(r'^_internal/create-resource/do/$', views.create_resource_new_workflow),
    url(r'^_internal/resend_verification_email/$', views.resend_verification_email),
)
