from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import MpMetadata, ModelProgramMetaData


class MpMetaDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = MpMetadata
        fields = ('modelVersion', 'modelProgramLanguage', 'modelOperatingSystem',
                  'modelReleaseDate', 'modelWebsite', 'modelCodeRepository',
                  'modelReleaseNotes', 'modelDocumentation', 'modelSoftware',
                  'modelEngine')


class ModelProgramMetaDataSerializer(CoreMetaDataSerializer):
    program = MpMetaDataSerializer(required=False, many=False)

    class Meta:
        model = ModelProgramMetaData
