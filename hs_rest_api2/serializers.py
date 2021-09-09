from rest_framework.serializers import Serializer

from hsmodels.schemas import ResourceMetadata, GeographicFeatureMetadata, GeographicRasterMetadata, \
    MultidimensionalMetadata, SingleFileMetadata, FileSetMetadata, TimeSeriesMetadata, ReferencedTimeSeriesMetadata


class ResourceMetadataSerializer(Serializer):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ResourceMetadata.schema()


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
