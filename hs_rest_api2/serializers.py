from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework.serializers import Serializer

from hsmodels.schemas import ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, \
    MultidimensionalMetadata, SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata

from hsmodels.schemas.resource import ResourceMetadataIn


class ResourceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ResourceMetadata.schema()


class ResourceMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ResourceMetadataIn.schema()


class GeographicFeatureMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = GeographicFeatureMetadata.schema()


class GeographicRasterMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = GeographicRasterMetadata.schema()


class MultidimensionalMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = MultidimensionalMetadata.schema()


class SingleFileMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = SingleFileMetadata.schema()


class FileSetMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = FileSetMetadata.schema()


class TimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = TimeSeriesMetadata.schema()


class ReferencedTimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ReferencedTimeSeriesMetadata.schema()


class NestedSchemaGenerator(OpenAPISchemaGenerator):
    """
    Injects hsmodels metadata models nested definitions into the root definitions swagger instance
    """

    def get_schema(self, request=None, public=False):
        swagger = super(NestedSchemaGenerator, self).get_schema(request, public)
        for model in [ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, MultidimensionalMetadata,
                      SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata]:
            schema = model.schema()
            for d in schema['definitions']:
                swagger.definitions.update({d: schema['definitions'][d]})
        return swagger

