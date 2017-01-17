import logging

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import status
from rest_framework import generics
from rest_framework import serializers

from hs_core import hydroshare
from hs_core.models import Contributor, CoreMetaData, Coverage, Creator, Date, \
    ExternalProfileLink, Format, FundingAgency, Identifier, Subject, Source, Relation
from hs_core.views import utils as view_utils
from hs_core.views.utils import ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)


class ExternalProfileLinkSerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    url = serializers.URLField(required=False)
    object_id = serializers.IntegerField(required=False)
    # content_type = models.ForeignKey(ContentType)
    # content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        model = ExternalProfileLink


class PartySerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.URLField(required=False)
    organization = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    homepage = serializers.URLField(required=False)
    external_links = serializers = ExternalProfileLinkSerializer(required=False, many=True)

    class Meta:
        model = Creator
        fields = {'name', 'description', 'organization', 'email',
                  'address', 'phone', 'homepage', 'external_links'}


class CreatorSerializer(PartySerializer):
    order = serializers.IntegerField(required=False)

    class Meta:
        model = Contributor


class DateSerializer(serializers.Serializer):
    # term = 'Date'
    type = serializers.CharField(required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)

    class Meta:
        model = Date


class CoverageSerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    value = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Coverage

    def get_value(self, obj):
        return obj.value


class FormatSerializer(serializers.Serializer):
    value = serializers.CharField(required=False)

    class Meta:
        model = Format


class FundingAgencySerializer(serializers.Serializer):
    agency_name = serializers.CharField()
    award_title = serializers.CharField(required=False)
    award_number = serializers.CharField(required=False)
    agency_url = serializers.URLField(required=False)

    class Meta:
        model = FundingAgency


class IdentifierSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    url = serializers.URLField(required=False)

    class Meta:
        model = Identifier


class SubjectSerializer(serializers.Serializer):
    value = serializers.CharField(required=False)

    class Meta:
        model = Subject


class SourceSerializer(serializers.Serializer):
    derived_from = serializers.CharField(required=False)

    class Meta:
        model = Source


class RelationSerializer(serializers.Serializer):
    type = serializers.CharField(required=False)
    value = serializers.CharField(required=False)

    class Meta:
        model = Relation


class CoreMetaDataSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    creators = CreatorSerializer(required=False, many=True)
    contributors = PartySerializer(required=False, many=True)
    coverages = CoverageSerializer(required=False, many=True)
    dates = DateSerializer(required=False, many=True)
    description = serializers.CharField(required=False)
    formats = FormatSerializer(required=False, many=True)
    funding_agencies = FundingAgencySerializer(required=False, many=True)
    identifiers = IdentifierSerializer(required=False, many=True)
    language = serializers.CharField(required=False)
    rights = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    publisher = serializers.CharField(required=False)
    sources = SourceSerializer(required=False, many=True)
    subjects = SubjectSerializer(required=False, many=True)
    relations = RelationSerializer(required=False, many=True)

    class Meta:
        model = CoreMetaData


class MetadataElementsRetrieveUpdate(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve resource science (Dublin Core) metadata

    REST URL: /hsapi/resource/{pk}/scimeta/elements/
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: resource science metadata as JSON document
    :rtype: str
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}

    REST URL: /hsapi/resource/{pk}/scimeta/elements/
    HTTP method: PUT

    :type pk: str
    :param pk: id of the resource
    :type request: JSON formatted string
    :param request: resource metadata
    :return: updated resource science metadata as JSON document
    :rtype: str
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return json format: {parameter-1': ['error message-1'],
    'parameter-2': ['error message-2'], .. }
    """
    ACCEPT_FORMATS = ('application/json',)

    allowed_methods = ('GET', 'PUT')

    serializer_class = CoreMetaDataSerializer

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)
        serializer = CoreMetaDataSerializer(resource.metadata)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        # Update science metadata
        view_utils.authorize(
            request, pk,
            needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)

        metadata = []
        put_data = request.data.copy()
        keys_to_update = put_data.keys()

        try:
            if 'title' in keys_to_update:
                metadata.append({"title": {"value": put_data.pop('title')}})

            if 'creators' in keys_to_update:
                for creator in put_data.pop('creators'):
                    metadata.append({"creator": creator})

            if 'contributors' in keys_to_update:
                for contributor in put_data.pop('contributors'):
                    metadata.append({"contributor": contributor})

            if 'coverages' in keys_to_update:
                for coverage in put_data.pop('coverages'):
                    metadata.append({"coverage": coverage})

            if 'dates' in keys_to_update:
                for date in put_data.pop('dates'):
                    metadata.append({"date": date})

            if 'description' in keys_to_update:
                metadata.append({"description": {"abstract": put_data.pop('description')}})

            if 'language' in keys_to_update:
                metadata.append({"language": {"code": put_data.pop('language')}})

            if 'rights' in keys_to_update:
                metadata.append({"rights": {"statement": put_data.pop('rights')}})

            if 'sources' in keys_to_update:
                for source in put_data.pop('sources'):
                    metadata.append({"source": source})

            if 'subjects' in keys_to_update:
                for subject in put_data.pop('subjects'):
                    metadata.append({"subject": {"value": subject['value']}})

            hydroshare.update_science_metadata(pk=pk, metadata=metadata)
        except Exception as ex:
            error_msg = {
                'resource': "Resource metadata update failed: %s, %s"
                            % ex.__class__ % ex.message
            }
            raise ValidationError(detail=error_msg)

        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)
        serializer = CoreMetaDataSerializer(resource.metadata)
        return Response(data=serializer.data, status=status.HTTP_202_ACCEPTED)
