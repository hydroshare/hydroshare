import json

import jsonschema
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import serializers

from hs_core.models import Coverage
from .models.model_program import ModelProgramResourceFileType, ModelProgramLogicalFile

_IN_DATE_FORMAT = "%Y-%m-%d"  # OpenAPI uses this date format for date field in the example input JSON data
_OUT_DATE_FORMAT = "%m/%d/%Y"


class TemporalCoverageSerializer((serializers.Serializer)):
    start = serializers.DateField(required=True, format=_OUT_DATE_FORMAT, input_formats=[_IN_DATE_FORMAT],
                                  help_text="Temporal coverage start date (YYYY-MM-DD)")
    end = serializers.DateField(required=True, format=_OUT_DATE_FORMAT, input_formats=[_IN_DATE_FORMAT],
                                help_text="Temporal coverage end date (YYYY-MM-DD)")


class SpatialCoverageSerializer((serializers.Serializer)):
    type = serializers.ChoiceField(choices=["point", "box"])
    units = serializers.CharField(max_length=100, help_text="Units of measurement for bounding box co-ordinates")
    name = serializers.CharField(required=False, max_length=100, help_text="Name of the place")
    north = serializers.FloatField(help_text="North co-ordinate")
    east = serializers.FloatField(help_text="East co-ordinate")
    west = serializers.FloatField(required=False, help_text="West co-ordinate (required if the coverage type is box)")
    south = serializers.FloatField(required=False, help_text="South co-ordinate (required if the coverage type is box)")

    def validate(self, data):
        if data:
            try:
                Coverage.validate_coverage_type_value_attributes(coverage_type=data['type'], value_dict=data,
                                                                 use_limit_postfix=False)
            except ValidationError as ex:
                raise serializers.ValidationError(str(ex))
        return data


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

    def validate(self, data):
        """Check for empty request body"""

        if not data:
            raise serializers.ValidationError("No metadata was provided to update")
        return data


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
    version = serializers.CharField(required=False, max_length=255, allow_blank=True,
                                    help_text='The software version or build number of the model')
    programming_languages = serializers.ListField(required=False, child=serializers.CharField(max_length=100),
                                                  allow_empty=True,
                                                  help_text="The programming language(s) that the model is written in")
    operating_systems = serializers.ListField(required=False, child=serializers.CharField(max_length=100),
                                              allow_empty=True,
                                              help_text="Compatible operating systems to setup and run the model")
    program_schema_json = serializers.JSONField(required=False, allow_null=True,
                                                help_text='Metadata schema as JSON data for model program aggregation')
    release_date = serializers.DateField(required=False, allow_null=True, format=_OUT_DATE_FORMAT,
                                         input_formats=[_IN_DATE_FORMAT],
                                         help_text='The date that this version of the model was released (YYYY-MM-DD)')
    website = serializers.URLField(required=False, allow_blank=True, max_length=255,
                                   help_text='A URL to the website maintained by the model developers')
    code_repository = serializers.URLField(required=False, allow_blank=True, max_length=255,
                                           help_text='A URL to the source code repository (e.g. git, mercurial, svn)')
    program_file_types = ModelProgramResourceFileTypeSerializer(many=True, required=False, default=None,
                                                                allow_null=True)

    def validate_program_schema_json(self, value):
        """Check that the metadata schema is valid."""

        if value:
            try:
                meta_schema_json = json.dumps(value)
            except Exception as ex:
                raise serializers.ValidationError(f"Metadata schema is not valid JSON. Error:{str(ex)}")
            # validate schema json here against the hs schema validator
            meta_schema_dict, validation_errors = ModelProgramLogicalFile.validate_meta_schema(meta_schema_json)
            if validation_errors:
                err_msg = ", ".join(validation_errors)
                raise serializers.ValidationError(f"Metadata schema is not valid. Error:{err_msg}")

            return meta_schema_dict
        return value

    def validate_program_file_types(self, value):
        """
        Check that the resource file exists and no duplicates in the request for program_file_types.
        """
        mp_aggr = self.context.get('mp_aggr')
        # check that are no duplicates
        seen = set()
        for ft_item_dict in value:
            ft_item_tuple = tuple(ft_item_dict.items())
            if ft_item_tuple in seen:
                raise serializers.ValidationError(f"Duplicate program_file_types:{ft_item_dict}")
            seen.add(ft_item_tuple)

        # check that the specified file paths are files of the aggregation
        valid_file_paths = [res_file.short_path for res_file in mp_aggr.files.all()]
        for ft_item in value:
            if ft_item['file_path'] not in valid_file_paths:
                raise serializers.ValidationError(f"Invalid file path:{ft_item['file_path']}")

        return value

    def update(self, mp_aggr, validated_data):
        """Updates the metadata for a model program aggregation."""

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
        data['title'] = mp_aggr.dataset_name
        data['keywords'] = mp_aggr.metadata.keywords
        data['additional_metadata'] = mp_aggr.metadata.extra_metadata
        data['version'] = mp_aggr.metadata.version
        data['website'] = mp_aggr.metadata.website
        data['code_repository'] = mp_aggr.metadata.code_repository
        if mp_aggr.metadata.release_date:
            data['release_date'] = mp_aggr.metadata.release_date.strftime(_OUT_DATE_FORMAT)
        else:
            data['release_date'] = mp_aggr.metadata.release_date

        data['operating_systems'] = mp_aggr.metadata.operating_systems
        data['programming_languages'] = mp_aggr.metadata.programming_languages
        data['program_schema_json'] = mp_aggr.metadata_schema_json
        mp_file_types = []
        for mp_file in mp_aggr.metadata.mp_file_types.all():
            mp_file_type_name = ModelProgramResourceFileType.type_name_from_type(mp_file.file_type)
            mp_file_types.append({'file_type': mp_file_type_name, 'file_path': mp_file.res_file.short_path})
        data['program_file_types'] = mp_file_types
        return data


class ModelInstanceMetaSerializer(BaseAggregationMetaSerializer):
    temporal_coverage = TemporalCoverageSerializer(required=False, help_text="Temporal coverage")
    spatial_coverage = SpatialCoverageSerializer(required=False, help_text="Spatial coverage")
    has_model_output = serializers.BooleanField(required=False,
                                                help_text="If the aggregation contains model output files")
    executed_by = serializers.CharField(required=False, allow_blank=True,
                                        help_text="Relative path of the model program aggregation "
                                                  "used for executing this model instance aggregation")
    metadata_json = serializers.JSONField(required=False, help_text="Schema-based metadata")

    def validate_executed_by(self, value):
        """Validate the path for the model program aggregation."""

        resource = self.context.get('resource')
        if value:
            try:
                aggr = resource.get_aggregation_by_name(value)
                if not aggr.is_model_program:
                    raise serializers.ValidationError(f"Specified aggregation:{value} is not a model "
                                                      f"program aggregation")
            except ObjectDoesNotExist:
                raise serializers.ValidationError(f"No model program aggregation was found for the path:{value}")
            return aggr
        return value

    def validate_metadata_json(self, value):
        """Validate json data against the schema"""

        if value:
            try:
                json.dumps(value)
            except Exception as ex:
                raise serializers.ValidationError(f"Metadata is not valid JSON. Error:{str(ex)}")
            # validate against the the schema
            mi_aggr = self.context.get('mi_aggr')
            if not mi_aggr.metadata_schema_json:
                raise serializers.ValidationError("Metadata schema is missing")

            meta_json = value
            try:
                jsonschema.Draft4Validator(mi_aggr.metadata_schema_json).validate(meta_json)
            except jsonschema.ValidationError as ex:
                raise serializers.ValidationError(f"Invalid metadata. Error:{str(ex)}")

        return value

    def update(self, mi_aggr, validated_data):
        """Updates the metadata for a model instance aggregation."""

        mi_aggr.dataset_name = validated_data.get('title', mi_aggr.dataset_name)
        mi_aggr.metadata.keywords = validated_data.get('keywords', mi_aggr.metadata.keywords)
        mi_aggr.metadata.extra_metadata = validated_data.get('additional_metadata', mi_aggr.metadata.extra_metadata)
        mi_aggr.metadata.has_model_output = validated_data.get('has_model_output', mi_aggr.metadata.has_model_output)
        executed_by = validated_data.get('executed_by', None)
        if isinstance(executed_by, ModelProgramLogicalFile):
            mi_aggr.metadata.executed_by = executed_by
            if executed_by.metadata_schema_json and not mi_aggr.metadata_schema_json:
                mi_aggr.metadata_schema_json = executed_by.metadata_schema_json
        elif isinstance(executed_by, str):
            mi_aggr.metadata.executed_by = None

        mi_aggr.metadata.metadata_json = validated_data.get('metadata_json', mi_aggr.metadata.metadata_json)
        spatial_coverage = validated_data.get('spatial_coverage', None)
        if spatial_coverage is not None:
            if spatial_coverage:
                cove_type = spatial_coverage.pop('type')
                if cove_type == 'point':
                    spatial_coverage.pop('south', None)
                    spatial_coverage.pop('west', None)
                else:
                    spatial_coverage['northlimit'] = spatial_coverage.pop('north')
                    spatial_coverage['eastlimit'] = spatial_coverage.pop('east')
                    spatial_coverage['southlimit'] = spatial_coverage.pop('south')
                    spatial_coverage['westlimit'] = spatial_coverage.pop('west')
                if mi_aggr.metadata.spatial_coverage:
                    mi_aggr.metadata.update_element('coverage', mi_aggr.metadata.spatial_coverage.id, type=cove_type,
                                                    value=spatial_coverage)
                else:
                    mi_aggr.metadata.create_element('coverage', type=cove_type, value=spatial_coverage)
            elif mi_aggr.metadata.spatial_coverage:
                mi_aggr.metadata.spatial_coverage.delete()

        temporal_coverage = validated_data.get('temporal_coverage', None)
        if temporal_coverage is not None:
            if temporal_coverage:
                temporal_coverage['start'] = temporal_coverage['start'].strftime(_OUT_DATE_FORMAT)
                temporal_coverage['end'] = temporal_coverage['end'].strftime(_OUT_DATE_FORMAT)
                if mi_aggr.metadata.temporal_coverage:
                    mi_aggr.metadata.update_element('coverage', mi_aggr.metadata.temporal_coverage.id, type='period',
                                                    value=temporal_coverage)
                else:
                    mi_aggr.metadata.create_element('coverage', type='period', value=temporal_coverage)
            elif mi_aggr.metadata.temporal_coverage:
                mi_aggr.metadata.temporal_coverage.delete()

        mi_aggr.metadata.is_dirty = True
        mi_aggr.metadata.save()
        mi_aggr.save()
        return mi_aggr

    @staticmethod
    def serialize(mi_aggr):
        """Helper to serialize the metadata for a model instance aggregation."""

        data = dict()
        data['title'] = mi_aggr.dataset_name
        data['keywords'] = mi_aggr.metadata.keywords
        data['additional_metadata'] = mi_aggr.metadata.extra_metadata
        if mi_aggr.metadata.executed_by:
            data['executed_by'] = mi_aggr.metadata.executed_by.aggregation_name
        else:
            data['executed_by'] = ""
        data['has_model_output'] = mi_aggr.metadata.has_model_output
        data['metadata_json'] = mi_aggr.metadata.metadata_json
        data['metadata_schema'] = mi_aggr.metadata_schema_json
        temporal_coverage = mi_aggr.metadata.temporal_coverage
        if temporal_coverage is not None:
            data['temporal_coverage'] = temporal_coverage.value
        else:
            data['temporal_coverage'] = {}
        spatial_coverage = mi_aggr.metadata.spatial_coverage
        if spatial_coverage is not None:
            coverage_data = spatial_coverage.value
            coverage_data['type'] = spatial_coverage.type
            data['spatial_coverage'] = coverage_data
        else:
            data['spatial_coverage'] = {}

        return data
