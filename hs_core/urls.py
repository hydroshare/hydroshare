from django.conf.urls import patterns, url
from hs_core import views

urlpatterns = patterns('',

    # resource API
     url(r'^resource/types/$', views.resource_rest_api.ResourceTypes.as_view(),
        name='list_resource_types'),

     # DEPRECATED: use from above instead
     url(r'^resourceTypes/$', views.resource_rest_api.ResourceTypes.as_view(),
        name='DEPRECATED_list_resource_types'),

    # DEPRECATED: use GET /resource/ instead 
    url(r'^resourceList/$', views.resource_rest_api.ResourceList.as_view(),
        name='DEPRECATED_list_resources'),

    url(r'^resource/$', views.resource_rest_api.ResourceListCreate.as_view(),
        name='list_create_resource'),

    # Public endpoint for resource flags
    url(r'^resource/(?P<pk>[0-9a-f-]+)/flag/$', views.set_resource_flag_public,
        name='public_set_resource_flag'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/$', views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),

    # Create new version of a resource
    url(r'^resource/(?P<pk>[0-9a-f-]+)/version/$', views.create_new_version_resource_public,
        name='new_version_resource_public'),

    # public copy resource endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/copy/$', views.copy_resource_public, name='copy_resource_public'),

    # DEPRECATED: use form above instead
    url(r'^resource/accessRules/(?P<pk>[0-9a-f-]+)/$', views.resource_rest_api.AccessRulesUpdate.as_view(),
        name='DEPRECATED_update_access_rules'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/sysmeta/$', views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_system_metadata'),

    # DEPRECATED: use from above instead
    url(r'^sysmeta/(?P<pk>[0-9a-f-]+)/$', views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='DEPRECATED_get_system_metadata'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/$', views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='get_update_science_metadata'),

    # Resource metadata editing
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/elements/$', views.resource_metadata_rest_api.MetadataElementsRetrieveUpdate.as_view(),
        name='get_update_science_metadata_elements'),

    # Update key-value metadata
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/custom/$', views.update_key_value_metadata_public,
        name='update_custom_metadata'),

    # DEPRECATED: use from above instead
    url(r'^scimeta/(?P<pk>[0-9a-f-]+)/$', views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='DEPRECATED_get_update_science_metadata'),

    url(r'^resource/(?P<pk>[A-z0-9]+)/map/$', views.resource_rest_api.ResourceMapRetrieve.as_view(),
        name='get_resource_map'),

    # Unused. See ResourceFileListCreate. This is now implemented there.
    # Older version based upon polymorphism of ResourceFileCRUD. 
    # url(r'^resource/(?P<pk>[A-z0-9]+)/files/$', 
    #     views.resource_rest_api.ResourceFileCRUD.as_view(),
    #     name='add_resource_file'),

    # Patterns are now checked in the view class.
    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/(?P<pathname>.+)/$',
        views.resource_rest_api.ResourceFileCRUD.as_view(), 
        name='get_update_delete_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/$', 
        views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='list_create_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/folders/(?P<pathname>.*)/$', 
        views.resource_folder_rest_api.ResourceFolders.as_view(),
        name='list_manipulate_folders'),

    # public unzip endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/unzip/(?P<pathname>.*)/$',
        views.resource_folder_hierarchy.data_store_folder_unzip_public),

    # public zip folder endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/zip/$',
        views.resource_folder_hierarchy.data_store_folder_zip_public),

    # public move or rename
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/move-or-rename/$',
        views.resource_folder_hierarchy.data_store_file_or_folder_move_or_rename_public),

    # DEPRECATED: use form above instead. Added unused POST for simplicity
    url(r'^resource/(?P<pk>[0-9a-f-]+)/file_list/$', 
        views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='DEPRECATED_get_resource_file_list'),

    url(r'^taskstatus/(?P<task_id>[A-z0-9\-]+)/$',
        views.resource_rest_api.CheckTaskStatus.as_view(),
        name='get_task_status'),

    url(r'^userInfo/$',
        views.user_rest_api.UserInfo.as_view(), name='get_logged_in_user_info'),

    # Resource Access
    url(r'^resource/(?P<pk>[0-9a-f-]+)/access/$',
        views.resource_access_api.ResourceAccessUpdateDelete.as_view(),
        name='get_update_delete_resource_access'),

    # internal API

    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/add-files-to-resource/$',
        views.add_files_to_resource, name='add_files_to_resource'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/(?P<element_name>[A-z]+)/add-metadata/$',
        views.add_metadata_element, name='add_metadata_element'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/update-metadata/$',
        views.update_metadata_element, name='update_metadata_element'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/(?P<element_name>[A-z]+)/(?P<element_id>[A-z0-9]+)/delete-metadata/$',
        views.delete_metadata_element, name='delete_metadata_element'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/update-key-value-metadata/$',
        views.update_key_value_metadata, name="update_key_value_metadata"),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/delete-resource-file/(?P<f>[0-9]+)/$',
        views.delete_file, name='delete_file'),
    url(r'^_internal/(?P<shortkey>[A-z0-9]+)/delete-multiple-files/$',
        views.delete_multiple_files, name='delete_multiple_files'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/delete-resource/$',
        views.delete_resource, name='delete_resource'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/create-new-version-resource/$',
        views.create_new_version_resource, name='create_resource_version'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/copy-resource/$', views.copy_resource,
        name='copy_resource'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/rep-res-bag-to-irods-user-zone/$', views.rep_res_bag_to_irods_user_zone),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/set-resource-flag/$',
        views.set_resource_flag, name='set_resource_flag'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/share-resource-with-user/(?P<privilege>[a-z]+)/(?P<user_id>[0-9]+)/$',
        views.share_resource_with_user, name='share_resource_with_user'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/unshare-resource-with-user/(?P<user_id>[0-9]+)/$',
        views.unshare_resource_with_user),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/share-resource-with-group/(?P<privilege>[a-z]+)/(?P<group_id>[0-9]+)/$',
        views.share_resource_with_group, name='share_resource_with_group'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/unshare-resource-with-group/(?P<group_id>[0-9]+)/$',
        views.unshare_resource_with_group, name='unshare_resource_with_group'),
    url(r'^_internal/create-user-group/$', views.create_user_group, name='create_user_group'),
    url(r'^_internal/update-user-group/(?P<group_id>[0-9]+)$', views.update_user_group,
        name='update_user_group'),
    url(r'^_internal/delete-user-group/(?P<group_id>[0-9]+)$', views.delete_user_group,
        name='delete_user_group'),
    url(r'^_internal/restore-user-group/(?P<group_id>[0-9]+)$', views.restore_user_group,
        name='restore_user_group'),
    url(r'^_internal/share-group-with-user/(?P<group_id>[0-9]+)/(?P<user_id>[0-9]+)/(?P<privilege>[a-z]+)/$',
        views.share_group_with_user, name='share_group_with_user'),
    url(r'^_internal/unshare-group-with-user/(?P<group_id>[0-9]+)/(?P<user_id>[0-9]+)/$',
        views.unshare_group_with_user, name='unshare_group_with_user'),
    url(r'^_internal/make-group-membership-request/(?P<group_id>[0-9]+)/(?P<user_id>[0-9]+)/$',
        views.make_group_membership_request, name='make_group_membership_request'),
    url(r'^_internal/make-group-membership-request/(?P<group_id>[0-9]+)/$',
        views.make_group_membership_request, name='make_group_membership_request'),
    url(r'^_internal/act-on-group-membership-request/(?P<membership_request_id>[0-9]+)/(?P<action>[a-z]+)/$',
        views.act_on_group_membership_request, name='act_on_group_membership_request'),
    url(r'^_internal/group_membership/(?P<token>[-\w]+)/(?P<uidb36>[-\w]+)/(?P<membership_request_id>[0-9]+)/',
        views.group_membership,
        name='group_membership'),
    url(r'^_internal/get-user-or-group-data/(?P<user_or_group_id>[0-9]+)/(?P<is_group>[a-z]+)$', views.get_user_or_group_data, name='get_user_or_group_data'),
    url(r'^_internal/(?P<shortkey>[0-9a-f-]+)/publish/$', views.publish),
    url(r'^_internal/create-resource/$', views.create_resource_select_resource_type),
    url(r'^_internal/create-resource/do/$', views.create_resource, name='create_resource'),
    url(r'^_internal/verify-account/$', views.verify_account),
    url(r'^_internal/resend_verification_email/$', views.resend_verification_email),
    url(r'^_internal/(?P<resource_type>[A-z]+)/supported-file-types/$',
        views.get_supported_file_types_for_resource_type),
    url(r'^_internal/(?P<resource_type>[A-z]+)/allow-multiple-file/$',
        views.is_multiple_file_upload_allowed),
    url(r'^_internal/search/autocomplete/', "hs_core.views.autocomplete.autocomplete"),
    url(r'^_internal/data-store-structure/$', views.resource_folder_hierarchy.data_store_structure),
    url(r'^_internal/data-store-folder-zip/$',
        views.resource_folder_hierarchy.data_store_folder_zip),
    url(r'^_internal/data-store-folder-unzip/$',
        views.resource_folder_hierarchy.data_store_folder_unzip),
    url(r'^_internal/data-store-create-folder/$',
        views.resource_folder_hierarchy.data_store_create_folder),
    url(r'^_internal/data-store-move-or-rename/$',
        views.resource_folder_hierarchy.data_store_file_or_folder_move_or_rename),
    url(r'^_internal/data-store-delete-folder/$',
        views.resource_folder_hierarchy.data_store_remove_folder),
)
