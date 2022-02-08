from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from .models import AppHomePageUrl, RequestUrlBase, ToolVersion, SupportedResTypeChoices, \
    SupportedResTypes, SupportedSharingStatusChoices, SupportedSharingStatus, ToolIcon, \
    ToolMetaData, SupportedAggTypes, SupportedAggTypeChoices, SupportedFileExtensions, \
    RequestUrlBaseAggregation, RequestUrlBaseFile, MailingListUrl, TestingProtocolUrl, \
    HelpPageUrl, SourceCodeUrl, IssuesPageUrl, Roadmap


class SupportedResTypeChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedResTypeChoices
        fields = ('description',)


class SupportedAggTypeChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedAggTypeChoices
        fields = ('description',)


class SupportedSharingStatusChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedSharingStatusChoices
        fields = ('description',)


class SupportedFileExtensionsMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedFileExtensions
        fields = ('value',)


class AppHomePageUrlMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppHomePageUrl
        fields = ('value',)


class RequestUrlBaseMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUrlBase
        fields = ('value',)


class RequestUrlBaseAggregationMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUrlBaseAggregation
        fields = ('value',)


class RequestUrlBaseFileMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUrlBaseFile
        fields = ('value',)


class ToolVersionMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolVersion
        fields = ('value',)


class SupportedResTypesMetaDataSerializer(serializers.ModelSerializer):
    supported_res_types = SupportedResTypeChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = SupportedResTypes
        fields = ('supported_res_types', )


class SupportedAggTypesMetaDataSerializer(serializers.ModelSerializer):
    supported_agg_types = SupportedAggTypeChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = SupportedAggTypes
        fields = ('supported_agg_types', )


class SupportedSharingStatusMetaDataSerializer(serializers.ModelSerializer):
    sharing_status = SupportedSharingStatusChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = SupportedSharingStatus
        fields = ('sharing_status', )


class ToolIconMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolIcon
        fields = ('value', 'data_url')


class MailingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingListUrl
        fields = ('value',)


class TestingProtocolSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestingProtocolUrl
        fields = ('value',)


class HelpPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HelpPageUrl
        fields = ('value',)


class SourceCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceCodeUrl
        fields = ('value',)


class IssuesPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = IssuesPageUrl
        fields = ('value',)


class RoadmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roadmap
        fields = ('value',)


class ToolMetaDataSerializer(CoreMetaDataSerializer):
    url_base = RequestUrlBaseMetaDataSerializer(required=False, many=False)
    url_base_aggregation = RequestUrlBaseAggregationMetaDataSerializer(required=False, many=False)
    url_base_file = RequestUrlBaseFileMetaDataSerializer(required=False, many=False)
    version = ToolVersionMetaDataSerializer(required=False, many=False)
    supported_resource_types = SupportedResTypesMetaDataSerializer(required=False, many=False)
    supported_aggregation_types = SupportedAggTypesMetaDataSerializer(required=False, many=False)
    app_icon = ToolIconMetaDataSerializer(required=False, many=False)
    supported_sharing_statuses = SupportedSharingStatusMetaDataSerializer(required=False,
                                                                          many=False)
    supported_file_extensions = SupportedFileExtensionsMetaDataSerializer(required=False,
                                                                          many=False)
    app_home_page_url = AppHomePageUrlMetaDataSerializer(required=False, many=False)
    mailing_list_url = MailingListSerializer(required=False, many=False)
    testing_protocol_url = TestingProtocolSerializer(required=False, many=False)
    help_page_url = HelpPageSerializer(required=False, many=False)
    source_code_url = SourceCodeSerializer(required=False, many=False)
    issues_page_url = IssuesPageSerializer(required=False, many=False)
    roadmap = RoadmapSerializer(required=False, many=False)

    class Meta:
        model = ToolMetaData
