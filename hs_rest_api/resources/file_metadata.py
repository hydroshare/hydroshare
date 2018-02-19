import json

from rest_framework.response import Response
from rest_framework import generics
from rest_framework import serializers

from hs_core.models import ResourceFile, Coverage


# TODO: Once we upgrade past Django Rest Framework 3.3, this won't be necessary
class JSONSerializerField(serializers.Field):
    """ Serializer for JSONField -- required to make field writable"""

    def to_internal_value(self, data):
        return data

    def to_representation(self, value):
        return value


class FileMetaDataSerializer(serializers.Serializer):
    title = serializers.CharField()
    keywords = JSONSerializerField()
    spatial_coverage = JSONSerializerField()
    extra_metadata = JSONSerializerField()
    temporal_coverage = JSONSerializerField()


class FileMetaDataRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FileMetaDataSerializer
    allowed_methods = ('GET', 'PUT')

    def validate(self, data):
        if not resource_file.has_logical_file:
            raise serializers.ValidationError(u"Resource file has no logical file.")

    def get(self, request, pk, file_id):
        """ Get a resource file's metadata. """
        resource_file = ResourceFile.objects.get(id=file_id)

        if resource_file.metadata == None:
            return Response({}, status=404)

        # TODO: How to leverage serializer for this?
        return Response({
            "title": file_metadata.logical_file.dataset_name,
            "keywords": file_metadata.keywords,
            "spatial_coverage": file_metadata.spatial_coverage.value,
            "extra_metadata": file_metadata.extra_metadata,
            "temporal_coverage": file_metadata.temporal_coverage.value
        })

    def put(self, request, pk, file_id):
        """ Update a resource file's metadata """
        metadata_json = json.loads(request.body)
        file_serializer = FileMetaDataSerializer(metadata_json)

        title = file_serializer.data.pop("title", "")
        resource_file = ResourceFile.objects.get(id=file_id)
        resource_file.metadata.logical_file.dataset_name = title
        resource_file.metadata.logical_file.save()

        spatial_coverage = file_serializer.data.pop("spatial_coverage", {})
        Coverage.update(resource_file.metadata.spatial_coverage.id,
                        _value=json.dumps(spatial_coverage))

        temporal_coverage = file_serializer.data.pop("temporal_coverage", {})
        Coverage.update(resource_file.metadata.temporal_coverage.id,
                        _value=json.dumps(temporal_coverage))

        keywords = file_serializer.data.pop("keywords", [])
        extra_metadata = file_serializer.data.pop("extra_metadata", [])
        resource_file.metadata.extra_metadata = extra_metadata
        resource_file.metadata.keywords = keywords
        resource_file.metadata.save()

        # TODO: How to leverage serializer for this?
        file_metadata = resource_file.metadata
        return Response({
            "title": file_metadata.logical_file.dataset_name,
            "keywords": file_metadata.keywords,
            "spatial_coverage": file_metadata.spatial_coverage.value,
            "extra_metadata": file_metadata.extra_metadata,
            "temporal_coverage": file_metadata.temporal_coverage.value
        })
