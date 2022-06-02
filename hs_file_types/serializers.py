from rest_framework import serializers


class ModelProgramMetaTemplateSchemaSerializer(serializers.Serializer):
    meta_schema_filename = serializers.CharField(max_length=100, required=True,
                                                 help_text='list of template metadata schema filenames for model '
                                                           'program aggregation')
