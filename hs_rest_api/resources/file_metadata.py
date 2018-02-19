import json

from django.shortcuts import get_object_or_404

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
    title = serializers.CharField(required=False)
    keywords = JSONSerializerField(required=False)
    spatial_coverage = JSONSerializerField(required=False)
    extra_metadata = JSONSerializerField(required=False)
    temporal_coverage = JSONSerializerField(required=False)


class FileMetaDataRetrieveUpdateDestroy(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = FileMetaDataSerializer
    allowed_methods = ('GET', 'PUT')

    def get(self, request, pk, file_id):
        """ Get a resource file's metadata. """
        resource_file = get_object_or_404(ResourceFile, id=file_id)

        if resource_file.metadata is None or not resource_file.has_logical_file:
            return Response({}, status=404)

        title = resource_file.metadata.logical_file.dataset_name \
            if resource_file.metadata.logical_file else ""
        keywords = resource_file.metadata.keywords \
            if resource_file.metadata else []
        spatial_coverage = resource_file.metadata.spatial_coverage.value \
            if resource_file.metadata.spatial_coverage else {}
        extra_metadata = resource_file.metadata.extra_metadata \
            if resource_file.metadata else []
        spatial_coverage = resource_file.metadata.temporal_coverage.value if \
            resource_file.metadata.temporal_coverage else {}

        # TODO: How to leverage serializer for this?
        return Response({
            "title": title,
            "keywords": keywords,
            "spatial_coverage": spatial_coverage,
            "extra_metadata": extra_metadata,
            "temporal_coverage": spatial_coverage
        })

    def put(self, request, pk, file_id):
        """ Update a resource file's metadata """
        print(request.data)
        file_serializer = FileMetaDataSerializer(request.data)

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
