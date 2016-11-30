import logging
import json

from rest_framework.response import Response
from rest_framework import status
from rest_framework import generics
from rest_framework import serializers

from hs_core import hydroshare
from hs_core.models import Contributor, CoreMetaData, Coverage, Creator, Date, ExternalProfileLink, \
    Format, FundingAgency, Identifier, Subject, Source, Relation
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
        fields = {'name', 'description', 'organization', 'email', 'address', 'phone', 'homepage', 'external_links'}


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

    class Meta:
        model = Coverage


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
    Retrieve resource Dublin Core metadata

    REST URL: /hsapi/resource/{pk}/scimeta/elements/
    HTTP method: GET

    :type pk: str
    :param pk: id of the resource
    :return: resource metadata as JSON document
    :rtype: str
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id:pk'}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}

    REST URL: /hsapi/resource/{pk}/scimeta/elements/
    HTTP method: PUT

    :type pk: str
    :param pk: id of the resource
    :type metadata: json
    :param metadata: resource metadata
    :return: resource id
    :rtype: json of the format: {'resource_id':pk}
    :raises:
    NotFound: return json format: {'detail': 'No resource was found for resource id':pk}
    PermissionDenied: return json format: {'detail': 'You do not have permission to perform
    this action.'}
    ValidationError: return json format: {parameter-1': ['error message-1'],
    'parameter-2': ['error message-2'], .. }
    """
    ACCEPT_FORMATS = ('application/xml', 'application/rdf+xml')

    allowed_methods = ('GET', 'PUT')

    serializer_class = CoreMetaDataSerializer

    def get(self, request, pk):
        view_utils.authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA)
        resource = hydroshare.get_resource_by_shortkey(shortkey=pk)
        serializer = CoreMetaDataSerializer(resource.content_object)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    # def put(self, request, pk):
    #     # Update science metadata based on resourcemetadata.xml uploaded
    #     resource, authorized, user = view_utils.authorize(
    #         request, pk,
    #         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
    #         raises_exception=False)
    #     if not authorized:
    #         raise PermissionDenied()

    #     files = request.FILES.values()
    #     if len(files) == 0:
    #         error_msg = {'file': 'No resourcemetadata.xml file was found to update resource '
    #                              'metadata.'}
    #         raise ValidationError(detail=error_msg)
    #     elif len(files) > 1:
    #         error_msg = {'file': ('More than one file was found. Only one file, named '
    #                               'resourcemetadata.xml, '
    #                               'can be used to update resource metadata.')}
    #         raise ValidationError(detail=error_msg)

    #     scimeta = files[0]
    #     if scimeta.content_type not in self.ACCEPT_FORMATS:
    #         error_msg = {'file': ("Uploaded file has content type {t}, "
    #                               "but only these types are accepted: {e}.").format(
    #             t=scimeta.content_type, e=",".join(self.ACCEPT_FORMATS))}
    #         raise ValidationError(detail=error_msg)
    #     expect = 'resourcemetadata.xml'
    #     if scimeta.name != expect:
    #         error_msg = {'file': "Uploaded file has name {n}, but expected {e}.".format(
    #             n=scimeta.name, e=expect)}
    #         raise ValidationError(detail=error_msg)

    #     # Temp directory to store resourcemetadata.xml
    #     tmp_dir = tempfile.mkdtemp()
    #     try:
    #         # Fake the bag structure so that GenericResourceMeta.read_metadata_from_resource_bag
    #         # can read and validate the system and science metadata for us.
    #         bag_data_path = os.path.join(tmp_dir, 'data')
    #         os.mkdir(bag_data_path)
    #         # Copy new science metadata to bag data path
    #         scimeta_path = os.path.join(bag_data_path, 'resourcemetadata.xml')
    #         shutil.copy(scimeta.temporary_file_path(), scimeta_path)
    #         # Copy existing resource map to bag data path
    #         # (use a file-like object as the file may be in iRODS, so we can't
    #         #  just copy it to a local path)
    #         resmeta_path = os.path.join(bag_data_path, 'resourcemap.xml')
    #         with open(resmeta_path, 'wb') as resmeta:
    #             storage = get_file_storage()
    #             resmeta_irods = storage.open(AbstractResource.sysmeta_path(pk))
    #             shutil.copyfileobj(resmeta_irods, resmeta)

    #         resmeta_irods.close()

    #         try:
    #             # Read resource system and science metadata
    #             domain = Site.objects.get_current().domain
    #             rm = GenericResourceMeta.read_metadata_from_resource_bag(tmp_dir,
    #                                                                      hydroshare_host=domain)
    #             # Update resource metadata
    #             rm.write_metadata_to_resource(resource, update_title=True, update_keywords=True)
    #             create_bag_files(resource)
    #         except HsDeserializationDependencyException as e:
    #             msg = ("HsDeserializationDependencyException encountered when updating "
    #                    "science metadata for resource {pk}; depedent resource was {dep}.")
    #             msg = msg.format(pk=pk, dep=e.dependency_resource_id)
    #             logger.error(msg)
    #             raise ValidationError(detail=msg)
    #         except HsDeserializationException as e:
    #             raise ValidationError(detail=e.message)

    #         resource_modified(resource, request.user)
    #         return Response(data={'resource_id': pk}, status=status.HTTP_202_ACCEPTED)
    #     finally:
    #         shutil.rmtree(tmp_dir)
