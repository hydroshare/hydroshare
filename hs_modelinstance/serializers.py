from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import ModelOutput, ExecutedBy, ModelInstanceMetaData


class ModelOutputMetaDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ModelOutput
        fields = ('includes_output',)


class ExecutedByMetaDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ExecutedBy
        fields = ('modelProgramName', 'modelProgramIdentifier')


class ModelInstanceMetaDataSerializer(CoreMetaDataSerializer):
    model_output = ModelOutputMetaDataSerializer(required=False, many=False)
    executed_by = ExecutedByMetaDataSerializer(required=False, many=False)

    class Meta:
        model = ModelInstanceMetaData
