from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework.serializers import Serializer

from hsmodels.schemas import ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, \
    MultidimensionalMetadata, SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata

from hsmodels.schemas.resource import ResourceMetadataIn
from hsmodels.schemas.aggregations import GeographicFeatureMetadataIn, GeographicRasterMetadataIn, \
    MultidimensionalMetadataIn, SingleFileMetadataIn, FileSetMetadataIn, TimeSeriesMetadataIn, \
    ReferencedTimeSeriesMetadataIn, ModelProgramMetadata, ModelProgramMetadataIn, ModelInstanceMetadata, \
    ModelInstanceMetadataIn


class ResourceMetadataInForbidExtra(ResourceMetadataIn):

    class Config:
        extra = 'forbid'


class ResourceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ResourceMetadata.schema()


class ResourceMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ResourceMetadataInForbidExtra.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class GeographicFeatureMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = GeographicFeatureMetadata.schema()


class GeographicFeatureMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = GeographicFeatureMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class GeographicRasterMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = GeographicRasterMetadata.schema()


class GeographicRasterMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = GeographicRasterMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class MultidimensionalMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = MultidimensionalMetadata.schema()


class MultidimensionalMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = MultidimensionalMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class SingleFileMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = SingleFileMetadata.schema()


class SingleFileMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = SingleFileMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class FileSetMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = FileSetMetadata.schema()


class FileSetMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = FileSetMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class TimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = TimeSeriesMetadata.schema()


class TimeSeriesMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = TimeSeriesMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class ReferencedTimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ReferencedTimeSeriesMetadata.schema()


class ReferencedTimeSeriesMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ReferencedTimeSeriesMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class ModelProgramMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ModelProgramMetadata.schema()


class ModelProgramMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ModelProgramMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class ModelInstanceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ModelInstanceMetadata.schema()


class ModelInstanceMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ModelInstanceMetadataIn.schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = _schema


class NestedSchemaGenerator(OpenAPISchemaGenerator):
    """
    Injects hsmodels metadata models nested definitions into the root definitions swagger instance
    """

    def get_schema(self, request=None, public=False):
        swagger = super(NestedSchemaGenerator, self).get_schema(request, public)
        for model in [ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, MultidimensionalMetadata,
                      SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata]:
            schema = model.model_json_schema()
            for d in schema['$defs']:
                swagger.definitions.update({d: schema['$defs'][d]})
        return swagger
