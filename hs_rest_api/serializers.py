from rest_framework.serializers import Serializer, JSONField

from hsmodels.schemas import ResourceMetadata


class ResourceMetadataJSONField(JSONField):
    class Meta:
        fields = "__all__"
        swagger_schema_fields = ResourceMetadata.schema()

class ResourceMetadataSerializer(Serializer):
    metadata = ResourceMetadataJSONField()