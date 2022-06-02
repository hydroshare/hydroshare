import json
from rest_framework import serializers
from .models.model_program import ModelProgramResourceFileType, ModelProgramLogicalFile


class BaseAggregationMetaSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    keywords = serializers.ListField(required=False, child=serializers.CharField(max_length=100))
    additional_metadata = serializers.HStoreField(child=serializers.CharField(), allow_empty=True)

    def validate_keywords(self, value):
        """
        Check that there are no duplicates.
        """
        if value:
            if len(set(value)) != len(value):
                raise serializers.ValidationError("Duplicate keywords found")
        return value


class ModelProgramMetaTemplateSchemaSerializer(serializers.Serializer):
    meta_schema_filename = serializers.CharField(max_length=100, required=True,
                                                 help_text='List of available template metadata schema filenames for '
                                                           'model program aggregation')


class ModelProgramResourceFileTypeSerializer(serializers.Serializer):
    file_type = serializers.ChoiceField(choices=[choice[1] for choice in ModelProgramResourceFileType.CHOICES],
                                        required=False, help_text="Type of model program file")
    file_path = serializers.CharField(required=False, help_text="Relative path of the file in model program "
                                                                "aggregation")


class ModelProgramMetaSerializer(BaseAggregationMetaSerializer):
    name = serializers.CharField(required=False, max_length=255,
                                 help_text='The type/name of model program')
    version = serializers.CharField(required=False, max_length=255,
                                    help_text='The software version or build number of the model')
    programming_languages = serializers.ListField(required=False, child=serializers.CharField(max_length=100),
                                                  help_text="The programming language(s) that the model is written in")
    operating_systems = serializers.ListField(required=False, child=serializers.CharField(max_length=100),
                                              help_text="Compatible operating systems to setup and run the model")
    program_schema_json = serializers.JSONField(required=False,
                                                help_text='Metadata schema as JSON data for model program aggregation')
    release_date = serializers.DateField(required=False,
                                         help_text='The date that this version of the model was released')
    website = serializers.URLField(required=False, allow_blank=True, min_length=None, max_length=255,
                                   help_text='A URL to the website maintained by the model developers')
    code_repository = serializers.URLField(required=False, allow_blank=True, min_length=None, max_length=255,
                                           help_text='A URL to the source code repository (e.g. git, mercurial, svn)')
    program_file_types = ModelProgramResourceFileTypeSerializer(many=True, required=False, default=None)

    def validate_program_schema_json(self, value):
        """Check that the metadata schema is valid."""

        if value:
            try:
                meta_schema_json = json.dumps(value)
            except Exception as ex:
                raise serializers.ValidationError(f"Metadata schema is not valid. Error:{str(ex)}")
            # validate schema json here against the hs schema validator
            meta_schema_dict, validation_errors = ModelProgramLogicalFile.validate_meta_schema(meta_schema_json)
            if validation_errors:
                err_msg = ", ".join(validation_errors)
                raise serializers.ValidationError(f"Metadata schema is not valid. Error:{err_msg}")

            return meta_schema_dict
        return value

    def validate_program_file_types(self, value):
        """
        Check that the resource file exists.
        """
        mp_aggr = self.context.get('mp_aggr')
        valid_file_paths = [res_file.short_path for res_file in mp_aggr.files.all()]
        for ft_item in value:
            if ft_item['file_path'] not in valid_file_paths:
                raise serializers.ValidationError(f"Invalid file path:{ft_item['file_path']}")

        return value

    def update(self, mp_aggr, validated_data):
        """Updates the metadata for a model program aggregation."""

        mp_aggr.model_program_type = validated_data.get('name', mp_aggr.model_program_type)
        mp_aggr.dataset_name = validated_data.get('title', mp_aggr.dataset_name)
        mp_aggr.metadata.keywords = validated_data.get('keywords', mp_aggr.metadata.keywords)
        mp_aggr.metadata.extra_metadata = validated_data.get('additional_metadata', mp_aggr.metadata.extra_metadata)
        mp_aggr.metadata.version = validated_data.get('version', mp_aggr.metadata.version)
        mp_aggr.metadata.programming_languages = validated_data.get('programming_languages',
                                                                    mp_aggr.metadata.programming_languages)
        mp_aggr.metadata.operating_systems = validated_data.get('operating_systems',
                                                                mp_aggr.metadata.operating_systems)
        mp_aggr.metadata.release_date = validated_data.get('release_date', mp_aggr.metadata.release_date)
        mp_aggr.metadata.website = validated_data.get('website', mp_aggr.metadata.website)
        mp_aggr.metadata.code_repository = validated_data.get('code_repository', mp_aggr.metadata.code_repository)
        mp_aggr.metadata_schema_json = validated_data.get('program_schema_json', mp_aggr.metadata_schema_json)
        mp_aggr.metadata.is_dirty = True
        mp_aggr.metadata.save()
        mp_aggr.save()
        program_file_types = validated_data.get('program_file_types', None)
        if program_file_types is not None:
            res_file_path_map = {res_file.short_path: res_file for res_file in mp_aggr.files.all()}
            mp_aggr.metadata.mp_file_types.all().delete()
            for mp_file_item in program_file_types:
                if mp_file_item['file_path'] in res_file_path_map:
                    res_file = res_file_path_map[mp_file_item['file_path']]
                    mp_file_type = mp_file_item['file_type']
                    ModelProgramResourceFileType.create(file_type=mp_file_type, res_file=res_file,
                                                        mp_metadata=mp_aggr.metadata)
        return mp_aggr

    @staticmethod
    def serialize(mp_aggr):
        """Helper to serialize the metadata for a model program aggregation."""

        data = dict()
        data['name'] = mp_aggr.model_program_type
        data['title'] = mp_aggr.dataset_name
        data['keywords'] = mp_aggr.metadata.keywords
        data['extra_metadata'] = mp_aggr.metadata.extra_metadata
        data['version'] = mp_aggr.metadata.version
        data['website'] = mp_aggr.metadata.website
        data['code_repository'] = mp_aggr.metadata.code_repository
        data['release_date'] = mp_aggr.metadata.release_date
        data['operating_systems'] = mp_aggr.metadata.operating_systems
        data['programming_languages'] = mp_aggr.metadata.programming_languages
        data['metadata_schema'] = mp_aggr.metadata_schema_json
        mp_file_types = []
        for mp_file in mp_aggr.metadata.mp_file_types.all():
            mp_file_type_name = ModelProgramResourceFileType.type_name_from_type(mp_file.file_type)
            mp_file_types.append({'file_type': mp_file_type_name, 'file_path': mp_file.res_file.short_path})
        data['program_file_types'] = mp_file_types
        return data
