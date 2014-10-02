from django.conf.urls import patterns, url, include
from ga_resources import api, views

urlpatterns = patterns('',
    url(r'^resources/', include(api.resources.urls)),
    url(r'^styles/', include(api.styles.urls)),
    url(r'^layers/', include(api.layers.urls)),
    url(r'^wms/', views.WMS.as_view()),
    url(r'^(?P<layer>.*)/tms/(?P<z>[0-9]+)/(?P<x>[0-9]+)/(?P<y>[0-9]+)/', views.tms),
    url(r'^wfs/', views.WFS.as_view()),
    url(r'^download/(?P<slug>.*)$', views.download_file),
    url(r'^createpage/', views.create_page),
    url(r'^deletepage/', views.delete_page),
    url(r'^extent/(?P<slug>.*)/', views.extent),
    url(r'^kmz-features/(?P<slug>.*)/', views.kmz_features),
    url(r'^kmz-resource/(?P<slug>.*):(?P<filename>.*)/?', views.kmz_resource),
    url(r'^kmz-coverages/(?P<slug>.*)/', views.kmz_ground_overlays_json),
    
    # Page permissions
    
    url(r'^edit-groups/(?P<group>[0-9]+)/(?P<slug>.*)/', views.edit_groups),
    url(r'^view-groups/(?P<group>[0-9]+)/(?P<slug>.*)/', views.view_groups),
    url(r'^edit-users/(?P<user>[0-9]+)/(?P<slug>.*)/', views.edit_users),
    url(r'^view-users/(?P<user>[0-9]+)/(?P<slug>.*)/', views.view_users),
    url(r'^edit-groups/(?P<slug>.*)/', views.edit_groups),
    url(r'^view-groups/(?P<slug>.*)/', views.view_groups),
    url(r'^edit-users/(?P<slug>.*)/', views.edit_users),
    url(r'^view-users/(?P<slug>.*)/', views.view_users),
    url(r'^edit/', views.edit),

    # Data API

    url(r'^new/', views.create_dataset),
    url(r'^(?P<slug>[a-z0-9\-/]+)/schema/', views.schema),
    url(r'^(?P<slug>[a-z0-9\-/]+)/query/(?P<x1>[0-9\-.]+),(?P<y1>[0-9\-.]+),(?P<x2>[0-9\-.]+),(?P<y2>[0-9\-.]+)(?P<srid>;[0-9]+)?/',
        views.query),
    url(r'^(?P<slug>[a-z0-9\-/]+)/query/', views.query),
    url(r'^(?P<slug>[a-z0-9\-/]+)/add_column/', views.add_column),
    url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+):(?P<ogc_fid_end>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^(?P<slug>[a-z0-9\-/]+)/(?P<ogc_fid_start>[0-9]+),(?P<limit>[0-9]+)/', views.CRUDView.as_view()),
    url(r'^(?P<slug>[a-z0-9\-/]+)/fork/', views.derive_dataset),
    url(r'^(?P<slug>[a-z0-9\-/]+)/fork_geometry/', views.create_dataset_with_parent_geometry),
    url(r'^(?P<slug>[a-z0-9\-/]+)/', views.CRUDView.as_view()),
)
