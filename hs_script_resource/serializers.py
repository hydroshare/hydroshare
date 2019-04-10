from rest_framework import serializers

from hs_core.views.resource_metadata_rest_api import CoreMetaDataSerializer
from models import ScriptSpecificMetadata, ScriptMetaData


class ScriptSpecificMetadataSerializer(serializers.ModelSerializer):

    class Meta:
        model = ScriptSpecificMetadata
        fields = ('scriptLanguage', 'languageVersion', 'scriptVersion', 'scriptDependencies',
                  'scriptReleaseDate', 'scriptCodeRepository')


class ScriptMetaDataSerializer(CoreMetaDataSerializer):
    script_specific_metadata = ScriptSpecificMetadataSerializer(required=False, many=False)

    class Meta:
        model = ScriptMetaData
