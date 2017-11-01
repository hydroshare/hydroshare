from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import OriginalCoverage, BandInformation, CellInformation, RasterMetaData


class OrginalCoverageSerializer(serializers.Serializer):
    value = serializers.SerializerMethodField(required=False)

    class Meta:
        model = OriginalCoverage

    def get_value(self, obj):
        return obj.value


class BandInformationSerializer(serializers.ModelSerializer):

    class Meta:
        model = BandInformation
        fields = ('name', 'variableName', 'variableUnit', 'method', 'comment', 'noDataValue',
                  'maximumValue', 'minimumValue')


class CellInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CellInformation
        fields = ('name', 'rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellDataType')


class GeoRasterMetaDataSerializer(CoreMetaDataSerializer):
    originalCoverage = OrginalCoverageSerializer(required=False, many=False)
    cellInformation = CellInformationSerializer(required=False, many=False)
    bandInformations = BandInformationSerializer(required=False, many=True)

    class Meta:
        model = RasterMetaData
