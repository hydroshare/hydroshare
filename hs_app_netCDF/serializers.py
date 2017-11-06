from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import OriginalCoverage, Variable, NetcdfMetaData


class OrginalCoverageSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField(required=False)
    projection_string_type = serializers.CharField(required=False)
    projection_string_text = serializers.CharField(required=False)
    datum = serializers.CharField(required=False)

    class Meta:
        model = OriginalCoverage

    def get_value(self, obj):
        return obj.value


class VariableSerilalizer(serializers.ModelSerializer):

    class Meta:
        model = Variable
        fields = ('name', 'unit', 'type', 'shape', 'descriptive_name', 'method', 'missing_value')


class NetCDFMetaDataSerializer(CoreMetaDataSerializer):
    originalCoverage = OrginalCoverageSerializer(required=False, many=False)
    variables = VariableSerilalizer(required=False, many=True)

    class Meta:
        model = NetcdfMetaData
