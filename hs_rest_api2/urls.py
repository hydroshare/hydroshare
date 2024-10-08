from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .views.metadata import (
    file_set_metadata_json,
    geographic_feature_metadata_json,
    geographic_raster_metadata_json,
    model_instance_metadata_json,
    model_program_metadata_json,
    multidimensional_metadata_json,
    referenced_time_series_metadata_json,
    resource_metadata_json,
    single_file_metadata_json,
    time_series_metadata_json,
    csv_file_metadata_json
)

app_name = "hsapi2"
hsapi2_urlpatterns = [
    path('hsapi2/', include('hs_rest_api2.urls', namespace='hsapi2')),
]

schema_view_yasg = get_schema_view(
    openapi.Info(
        title="Hydroshare API",
        default_version='v2',
        description="Hydroshare Rest API",
        terms_of_service="https://help.hydroshare.org/about-hydroshare/policies/terms-of-use/",
        contact=openapi.Contact(email="help@cuahsi.org"),
    ),
    validators=[],
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    # Swagger Docs View
    re_path(r'^(?P<format>\.json|\.yaml)$', schema_view_yasg.without_ui(cache_timeout=None),
            name='schema-json'),
    path('', schema_view_yasg.with_ui('swagger', cache_timeout=None),
         name='schema-swagger-ui'),
    path('redoc/', schema_view_yasg.with_ui('redoc', cache_timeout=None), name='schema-redoc'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/$',
            resource_metadata_json,
            name='resource_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/GeographicFeature/(?P<aggregation_path>.*)$',
            geographic_feature_metadata_json,
            name='geographic_feature_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/GeographicRaster/(?P<aggregation_path>.*)$',
            geographic_raster_metadata_json,
            name='geographic_raster_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/TimeSeries/(?P<aggregation_path>.*)$',
            time_series_metadata_json,
            name='time_series_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/FileSet/(?P<aggregation_path>.*)$',
            file_set_metadata_json,
            name='file_set_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/Multidimensional/(?P<aggregation_path>.*)$',
            multidimensional_metadata_json,
            name='multidimensional_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/ReferencedTimeSeries/(?P<aggregation_path>.*)$',
            referenced_time_series_metadata_json,
            name='referenced_time_series_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/SingleFile/(?P<aggregation_path>.*)$',
            single_file_metadata_json,
            name='single_file_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/CSVFile/(?P<aggregation_path>.*)$',
            csv_file_metadata_json,
            name='csv_file_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/ModelInstance/(?P<aggregation_path>.*)$',
            model_instance_metadata_json,
            name='model_instance_metadata_json'),

    re_path(r'^resource/(?P<pk>[0-9a-f-]+)/json/ModelProgram/(?P<aggregation_path>.*)$',
            model_program_metadata_json,
            name='model_program_metadata_json'),
]
