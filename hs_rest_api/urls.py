from django.conf.urls import url

from hs_dictionary import views as dict_views
from hs_core import views as core_views
from hs_file_types import views as file_type_views
from hs_core.views.resource_folder_hierarchy import data_store_add_reference, \
    data_store_edit_reference_url

from .resources.file_metadata import FileMetaDataRetrieveUpdateDestroy

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from .views.hs_core import ShareResourceGroup, ShareResourceUser

schema_view_yasg = get_schema_view(
   openapi.Info(
      title="Hydroshare API",
      default_version='v1',
      description="Hydroshare Rest API",
      terms_of_service="https://help.hydroshare.org/about-hydroshare/policies/terms-of-use/",
      contact=openapi.Contact(email="help@cuahsi.org"),
   ),
   validators=[],
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger Docs View
    url(r'^(?P<format>\.json|\.yaml)$', schema_view_yasg.without_ui(cache_timeout=None),
        name='schema-json'),
    url(r'^$', schema_view_yasg.with_ui('swagger', cache_timeout=None),
        name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view_yasg.with_ui('redoc', cache_timeout=None), name='schema-redoc'),

    # resource API
    url(r'^resource/types/$', core_views.resource_rest_api.ResourceTypes.as_view(),
        name='list_resource_types'),

    url(r'^resource/$', core_views.resource_rest_api.ResourceListCreate.as_view(),
        name='list_create_resource'),

    # Public endpoint for resource flags
    url(r'^resource/(?P<pk>[0-9a-f-]+)/flag/$', core_views.set_resource_flag_public,
        name='public_set_resource_flag'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/$',
        core_views.resource_rest_api.ResourceReadUpdateDelete.as_view(),
        name='get_update_delete_resource'),

    # Create new version of a resource
    url(r'^resource/(?P<pk>[0-9a-f-]+)/version/$', core_views.create_new_version_resource_public,
        name='new_version_resource_public'),

    # public copy resource endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/copy/$',
        core_views.copy_resource_public, name='copy_resource_public'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/share/(?P<privilege>[a-z]+)/group/(?P<group_id>[\w.@+-]+)/$',
        ShareResourceGroup.as_view(), name='share_resource_group_public'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/share/(?P<privilege>[a-z]+)/user/(?P<user_id>[\w.@+-]+)/$',
        ShareResourceUser.as_view(), name='share_resource_user_public'),

    # DEPRECATED: use form above instead
    url(r'^resource/accessRules/(?P<pk>[0-9a-f-]+)/$',
        core_views.resource_rest_api.AccessRulesUpdate.as_view(),
        name='DEPRECATED_update_access_rules'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/sysmeta/$',
        core_views.resource_rest_api.SystemMetadataRetrieve.as_view(),
        name='get_system_metadata'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/$',
        core_views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='get_update_science_metadata'),

    # Resource metadata editing
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/elements/$',
        core_views.resource_metadata_rest_api.MetadataElementsRetrieveUpdate.as_view(),
        name='get_update_science_metadata_elements'),

    # Update key-value metadata
    url(r'^resource/(?P<pk>[0-9a-f-]+)/scimeta/custom/$',
        core_views.update_key_value_metadata_public,
        name='update_custom_metadata'),

    # DEPRECATED: use from above instead
    url(r'^scimeta/(?P<pk>[0-9a-f-]+)/$',
        core_views.resource_rest_api.ScienceMetadataRetrieveUpdate.as_view(),
        name='DEPRECATED_get_update_science_metadata'),

    url(r'^resource/(?P<pk>[A-z0-9]+)/map/$',
        core_views.resource_rest_api.ResourceMapRetrieve.as_view(),
        name='get_resource_map'),

    url(r'resource/(?P<pk>[0-9a-f-]+)/files/metadata/(?P<pathname>.*)/$',
        FileMetaDataRetrieveUpdateDestroy.as_view(), name="get_update_resource_file_metadata"),

    # Patterns are now checked in the view class.
    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/(?P<pathname>.+)/$',
        core_views.resource_rest_api.ResourceFileCRUD.as_view(),
        name='get_update_delete_resource_file'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/files/$',
        core_views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='list_create_resource_file'),

    url(r'^resource/data-store-add-reference/$',
        data_store_add_reference),

    url(r'^resource/data_store_edit_reference_url/$',
        data_store_edit_reference_url),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/folders/(?P<pathname>.*)/$',
        core_views.resource_folder_rest_api.ResourceFolders.as_view(),
        name='list_manipulate_folders'),

    # iRODS tickets
    # write disabled;change (?P<op>read) to (?P<op>read|write) when ready

    url(r'^resource/(?P<pk>[0-9a-f-]+)/ticket/(?P<op>read)/(?P<pathname>.*)/$',
        core_views.resource_ticket_rest_api.CreateResourceTicket.as_view(),
        name='create_ticket'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/ticket/bag/$',
        core_views.resource_ticket_rest_api.CreateBagTicket.as_view(),
        name='create_bag_ticket'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/ticket/(?P<ticket>.*)/$',
        core_views.resource_ticket_rest_api.ManageResourceTicket.as_view(),
        name='manage_ticket'),

    # public unzip endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/unzip/(?P<pathname>.*)/$',
        core_views.resource_folder_hierarchy.data_store_folder_unzip_public),

    # public zip folder endpoint
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/zip/$',
        core_views.resource_folder_hierarchy.data_store_folder_zip_public),

    # public move or rename
    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/move-or-rename/$',
        core_views.resource_folder_hierarchy.data_store_file_or_folder_move_or_rename_public),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/functions/set-file-type/(?P<file_path>.*)/'
        r'(?P<hs_file_type>[A-z]+)/$',
        file_type_views.set_file_type_public,
        name="set_file_type_public"),

    # DEPRECATED: use form above instead. Added unused POST for simplicity
    url(r'^resource/(?P<pk>[0-9a-f-]+)/file_list/$',
        core_views.resource_rest_api.ResourceFileListCreate.as_view(),
        name='DEPRECATED_get_resource_file_list'),

    url(r'^taskstatus/(?P<task_id>[A-z0-9\-]+)/$',
        core_views.resource_rest_api.CheckTaskStatus.as_view(),
        name='get_task_status'),

    url(r'^user/$',
        core_views.user_rest_api.UserInfo.as_view(), name='get_logged_in_user_info'),

    url(r'^userInfo/$',
        core_views.user_rest_api.UserInfo.as_view(), name='get_logged_in_user_info'),

    url(r'^dictionary/universities/$',
        dict_views.ListUniversities.as_view(), name="get_dictionary"),

    # Resource Access
    url(r'^resource/(?P<pk>[0-9a-f-]+)/access/$',
        core_views.resource_access_api.ResourceAccessUpdateDelete.as_view(),
        name='get_update_delete_resource_access'),


]
