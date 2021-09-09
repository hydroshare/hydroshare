from django.conf.urls import url

from .metadata import resource_metadata_json, geographic_feature_metadata_json

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

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
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Swagger Docs View
    url(r'^(?P<format>\.json|\.yaml)$', schema_view_yasg.without_ui(cache_timeout=None),
        name='schema-json'),
    url(r'^$', schema_view_yasg.with_ui('swagger', cache_timeout=None),
        name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view_yasg.with_ui('redoc', cache_timeout=None), name='schema-redoc'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/json/$',
        resource_metadata_json,
        name='resource_metadata_json'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/json/$',
        resource_metadata_json,
        name='resource_metadata_json'),

    url(r'^resource/(?P<pk>[0-9a-f-]+)/json/GeographicFeature/(?P<aggregation_path>.*)$',
        geographic_feature_metadata_json,
        name='resource_metadata_json'),
]
