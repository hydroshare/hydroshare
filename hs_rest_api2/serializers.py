import copy
import json

from drf_yasg.generators import OpenAPISchemaGenerator
from hsmodels.schemas import (FileSetMetadata, GeographicFeatureMetadata,
                              GeographicRasterMetadata,
                              MultidimensionalMetadata,
                              ReferencedTimeSeriesMetadata, ResourceMetadata,
                              SingleFileMetadata, TimeSeriesMetadata)
from hsmodels.schemas.aggregations import (FileSetMetadataIn,
                                           GeographicFeatureMetadataIn,
                                           GeographicRasterMetadataIn,
                                           ModelInstanceMetadata,
                                           ModelInstanceMetadataIn,
                                           ModelProgramMetadata,
                                           ModelProgramMetadataIn,
                                           MultidimensionalMetadataIn,
                                           ReferencedTimeSeriesMetadataIn,
                                           SingleFileMetadataIn,
                                           TimeSeriesMetadataIn)
from hsmodels.schemas.resource import ResourceMetadataIn
from pydantic import ConfigDict
from rest_framework.serializers import Serializer


def get_schema_open_api_v2(schema):
    # convert $defs to definitions to make it compatible with openapi v2
    schema_str = json.dumps(schema)
    schema_str = schema_str.replace('$defs', 'definitions')
    schema = json.loads(schema_str)
    updated_schema = copy.deepcopy(schema)
    for d in schema['definitions']:
        updated_schema.update({d: schema['definitions'][d]})
    return updated_schema


class ResourceMetadataInForbidExtra(ResourceMetadataIn):
    model_config = ConfigDict(extra="forbid")


class ResourceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(ResourceMetadata.model_json_schema())


class ResourceMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ResourceMetadataInForbidExtra.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class GeographicFeatureMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(GeographicFeatureMetadata.model_json_schema())


class GeographicFeatureMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = GeographicFeatureMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class GeographicRasterMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(GeographicRasterMetadata.model_json_schema())


class GeographicRasterMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = GeographicRasterMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class MultidimensionalMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(MultidimensionalMetadata.model_json_schema())


class MultidimensionalMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = MultidimensionalMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class SingleFileMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(SingleFileMetadata.model_json_schema())


class SingleFileMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = SingleFileMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class FileSetMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(FileSetMetadata.model_json_schema())


class FileSetMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = FileSetMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class TimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(TimeSeriesMetadata.model_json_schema())


class TimeSeriesMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = TimeSeriesMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class ReferencedTimeSeriesMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(ReferencedTimeSeriesMetadata.model_json_schema())


class ReferencedTimeSeriesMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ReferencedTimeSeriesMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class ModelProgramMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(ModelProgramMetadata.model_json_schema())


class ModelProgramMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ModelProgramMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class ModelInstanceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = get_schema_open_api_v2(ModelInstanceMetadata.model_json_schema())


class ModelInstanceMetadataInSerializer(Serializer):
    class Meta:
        fields = "__all__"
        _schema = ModelInstanceMetadataIn.model_json_schema()
        _schema['title'] = _schema['title'] + " In"
        swagger_schema_fields = get_schema_open_api_v2(_schema)


class NestedSchemaGenerator(OpenAPISchemaGenerator):
    """
    Injects hsmodels metadata models nested definitions into the root definitions swagger instance
    """

    def get_schema(self, request=None, public=False):
        swagger = super(NestedSchemaGenerator, self).get_schema(request, public)
        for model in [ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, MultidimensionalMetadata,
                      SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata]:
            schema = model.model_json_schema()
            schema = get_schema_open_api_v2(schema)

            for d in schema['definitions']:
                swagger.definitions.update({d: schema['definitions'][d]})
        return swagger
