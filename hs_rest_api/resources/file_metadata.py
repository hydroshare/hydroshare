from django.shortcuts import get_object_or_404

from rest_framework.response import Response
from rest_framework import generics
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound

from hs_core.models import ResourceFile

from hs_rest_api.permissions import CanViewOrEditResourceMetadata


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
    allowed_methods = ('GET', 'PUT',)
    permission_classes = (CanViewOrEditResourceMetadata,)

    def get(self, request, pk, file_id):
        """
        Get a resource file's metadata.

        ## Parameters
        * `id` - alphanumeric uuid of the resource, i.e. cde01b3898c94cdab78a2318330cf795
        * `file_id` - integer id of the resource file. You can use the `/hsapi/resource/{id}/files`
        to get these

        ## Returns
        ```
        {
            "keywords": [
                "keyword1",
                "keyword2"
            ],
            "spatial_coverage": {
                "units": "Decimal degrees",
                "east": -84.0465,
                "north": 49.6791,
                "name": "12232",
                "projection": "WGS 84 EPSG:4326"
            },
            "extra_metadata": {
                "extended1": "one"
            },
            "temporal_coverage": {
                "start": "2018-02-22",
                "end": "2018-02-24"
            },
            "title": "File Metadata Title"
        }
        ```
        """
        resource_file = get_object_or_404(ResourceFile, id=file_id)

        if resource_file.metadata is None or not resource_file.has_logical_file:
            raise NotFound()

        title = resource_file.metadata.logical_file.dataset_name \
            if resource_file.metadata.logical_file else ""
        keywords = resource_file.metadata.keywords \
            if resource_file.metadata else []
        spatial_coverage = resource_file.metadata.spatial_coverage.value \
            if resource_file.metadata.spatial_coverage else {}
        extra_metadata = resource_file.metadata.extra_metadata \
            if resource_file.metadata else {}
        temporal_coverage = resource_file.metadata.temporal_coverage.value if \
            resource_file.metadata.temporal_coverage else {}

        # TODO: How to leverage serializer for this?
        return Response({
            "title": title,
            "keywords": keywords,
            "spatial_coverage": spatial_coverage,
            "extra_metadata": extra_metadata,
            "temporal_coverage": temporal_coverage
        })

    def put(self, request, pk, file_id):
        """
        Update a resource file's metadata

        Accepts application/json encoding.

        ## Parameters
        * `id` - alphanumeric uuid of the resource, i.e. cde01b3898c94cdab78a2318330cf795
        * `file_id` - integer id of the resource file. You can use the `/hsapi/resource/{id}/files`
        to get these
        * `data` - see the "returns" section for formatting

        ## Returns
        ```
        {
            "keywords": [
                "keyword1",
                "keyword2"
            ],
            "spatial_coverage": {
                "units": "Decimal degrees",
                "east": -84.0465,
                "north": 49.6791,
                "name": "12232",
                "projection": "WGS 84 EPSG:4326"
            },
            "extra_metadata": {
                "extended1": "one"
            },
            "temporal_coverage": {
                "start": "2018-02-22",
                "end": "2018-02-24"
            },
            "title": "File Metadata Title"
        }
        ```
        """

        file_serializer = FileMetaDataSerializer(request.data)

        try:
            title = file_serializer.data.pop("title", "")
            resource_file = ResourceFile.objects.get(id=file_id)
            resource_file.metadata.logical_file.dataset_name = title
            resource_file.metadata.logical_file.save()

            spatial_coverage = file_serializer.data.pop("spatial_coverage", None)
            if spatial_coverage is not None:
                if resource_file.metadata.spatial_coverage is not None:
                    cov_id = resource_file.metadata.spatial_coverage.id
                    resource_file.metadata.update_element('coverage',
                                                          cov_id,
                                                          type='point',
                                                          value=spatial_coverage)
                elif resource_file.metadata.spatial_coverage is None:
                    resource_file.metadata.create_element('coverage', type="point",
                                                          value=spatial_coverage)

            temporal_coverage = file_serializer.data.pop("temporal_coverage", None)
            if temporal_coverage is not None:
                if resource_file.metadata.temporal_coverage is not None:
                    cov_id = resource_file.metadata.temporal_coverage.id
                    resource_file.metadata.update_element('coverage',
                                                          cov_id,
                                                          type='period',
                                                          value=temporal_coverage)
                elif resource_file.metadata.temporal_coverage is None:
                    resource_file.metadata.create_element('coverage', type="period",
                                                          value=temporal_coverage)

            keywords = file_serializer.data.pop("keywords", None)
            if keywords is not None:
                resource_file.metadata.keywords = keywords

            extra_metadata = file_serializer.data.pop("extra_metadata", None)
            if extra_metadata is not None:
                resource_file.metadata.extra_metadata = extra_metadata

            resource_file.metadata.save()
        except Exception as e:
            raise APIException(e)

        # TODO: How to leverage serializer for this?
        title = resource_file.metadata.logical_file.dataset_name \
            if resource_file.metadata.logical_file else ""
        keywords = resource_file.metadata.keywords \
            if resource_file.metadata else []
        spatial_coverage = resource_file.metadata.spatial_coverage.value \
            if resource_file.metadata.spatial_coverage else {}
        extra_metadata = resource_file.metadata.extra_metadata \
            if resource_file.metadata else {}
        temporal_coverage = resource_file.metadata.temporal_coverage.value if \
            resource_file.metadata.temporal_coverage else {}

        return Response({
            "title": title,
            "keywords": keywords,
            "spatial_coverage": spatial_coverage,
            "extra_metadata": extra_metadata,
            "temporal_coverage": temporal_coverage
        })
