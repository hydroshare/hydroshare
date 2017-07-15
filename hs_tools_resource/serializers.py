from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import AppHomePageUrl, RequestUrlBase, ToolVersion, SupportedResTypeChoices, \
    SupportedResTypes, SupportedSharingStatusChoices, SupportedSharingStatus, ToolIcon, \
    ToolMetaData


class SupportedResTypeChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedResTypeChoices
        fields = ('description',)


class SupportedSharingStatusChoicesMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedSharingStatusChoices
        fields = ('description',)


class AppHomePageUrlMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppHomePageUrl
        fields = ('value',)


class RequestUrlBaseMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestUrlBase
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


class SupportedSharingStatusMetaDataSerializer(serializers.ModelSerializer):
    sharing_status = SupportedSharingStatusChoicesMetaDataSerializer(required=False, many=True)

    class Meta:
        model = SupportedSharingStatus
        fields = ('sharing_status', )


class ToolIconMetaDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolIcon
        fields = ('value',)


class ToolMetaDataSerializer(CoreMetaDataSerializer):
    url_base = RequestUrlBaseMetaDataSerializer(required=False, many=False)
    version = ToolVersionMetaDataSerializer(required=False, many=False)
    supported_resource_types = SupportedResTypesMetaDataSerializer(required=False, many=False)
    app_icon = ToolIconMetaDataSerializer(required=False, many=False)
    supported_sharing_statuses = SupportedSharingStatusMetaDataSerializer(required=False,
                                                                          many=False)
    app_home_page_url = AppHomePageUrlMetaDataSerializer(required=False, many=False)

    class Meta:
        model = ToolMetaData
