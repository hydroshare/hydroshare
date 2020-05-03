import json
import jsonschema

from django import forms
from .models.model_program import ModelProgramResourceFileType
from .utils import get_model_program_aggregations


class ModelInstanceMetadataValidationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ModelInstanceMetadataValidationForm, self).__init__(*args, **kwargs)

    has_model_output = forms.BooleanField(required=False)
    executed_by = forms.IntegerField(required=False)

    def clean_executed_by(self):
        executed_by = self.cleaned_data['executed_by']
        user_selected_mp_aggr = None
        # if a model program has been selected then this form would have the id of that aggregation
        if executed_by > 0:
            user_mp_aggregations = get_model_program_aggregations(self.user)
            user_selected_mp_aggr = [mp_aggr for mp_aggr in user_mp_aggregations if mp_aggr.id == executed_by]
            if user_selected_mp_aggr:
                user_selected_mp_aggr = user_selected_mp_aggr[0]
            else:
                self.add_error("executed_by", "You don't have access to the selected model program aggregation")
        return user_selected_mp_aggr

    def update_metadata(self, metadata):
        executed_by = self.cleaned_data['executed_by']

        metadata.executed_by = executed_by
        metadata.has_model_output = self.cleaned_data['has_model_output']
        metadata.is_dirty = True
        metadata.save()


class ModelProgramMetadataValidationForm(forms.Form):
    version = forms.CharField(required=False, max_length=250)
    release_date = forms.DateField(required=False)
    website = forms.URLField(required=False, max_length=255)
    code_repository = forms.URLField(required=False, max_length=255)
    programming_languages = forms.CharField(required=False)
    operating_systems = forms.CharField(required=False)
    mi_json_schema = forms.CharField(required=False)
    mp_file_types = forms.CharField(max_length=255, required=False)
    mp_program_type = forms.CharField(max_length=255)

    def clean_version(self):
        version = self.cleaned_data['version'].strip()
        return version

    def clean_programming_languages(self):
        langauge_string = self.cleaned_data['programming_languages']
        if langauge_string:
            # generate a list of strings
            languages = langauge_string.split(',')
            languages = [lang.strip() for lang in languages]
            return languages
        return []

    def clean_operating_systems(self):
        os_string = self.cleaned_data['operating_systems']
        if os_string:
            # generate a list of strings
            op_systems = os_string.split(',')
            op_systems = [op.strip() for op in op_systems]
            return op_systems
        return []

    def clean_mp_file_types(self):
        mp_file_types_string = self.cleaned_data['mp_file_types']
        mp_file_types_dict = dict()
        if mp_file_types_string:
            mp_file_types = mp_file_types_string.split(";")
            for mp_file_type_string in mp_file_types:
                mp_file_type_lst = mp_file_type_string.split(":")
                if len(mp_file_type_lst) != 2:
                    self.add_error("mp_file_types", "Model program file type input data invalid")
                if mp_file_type_lst[1].lower() != "none":
                    mp_file_type = ModelProgramResourceFileType.type_from_string(mp_file_type_lst[1].lower())
                    if mp_file_type is None:
                        self.add_error("mp_file_types", "Not a valid model program file type")

                    mp_file_types_dict[mp_file_type_lst[0]] = mp_file_type
                else:
                    mp_file_types_dict[mp_file_type_lst[0]] = None
        return mp_file_types_dict

    def clean_mi_json_schema(self):
        json_schema_string = self.cleaned_data['mi_json_schema'].strip()
        json_schema = dict()
        is_schema_valid = True
        if json_schema_string:
            try:
                json_schema = json.loads(json_schema_string)
            except ValueError as exp:
                is_schema_valid = False
                self.add_error('mi_json_schema', "Not valid json data")

            if json_schema:
                try:
                    jsonschema.Draft4Validator.check_schema(json_schema)
                except jsonschema.SchemaError as ex:
                    is_schema_valid = False
                    self.add_error('mi_json_schema', "Not a valid json schema.{}".format(str(ex)))

            if is_schema_valid:
                # custom validation - hydroshare requirements
                # this custom validation requiring additional attributes are needed for making the jsoneditor form
                # generation at the front-end to work
                if 'additionalProperties' not in json_schema:
                    is_schema_valid = False
                    self.add_error('mi_json_schema',
                                   "Not a valid metadata schema. Attribute 'additionalProperties' "
                                   "is missing")
                elif json_schema['additionalProperties']:
                    is_schema_valid = False
                    self.add_error('mi_json_schema',
                                   "Not a valid metadata schema. Attribute 'additionalProperties' "
                                   "should bet set to 'false'")

                def validate_schema(schema_dict):
                    for k, v in schema_dict.items():
                        if isinstance(v, dict):
                            if k not in ('properties', 'items'):
                                # we need a title to use as label for the form field
                                if 'title' not in v:
                                    msg = "Not a valid metadata schema. Attribute 'title' is missing for {}".format(k)
                                    self.add_error('mi_json_schema', msg)
                                    break
                                elif len(v['title'].strip()) == 0:
                                    msg = "Not a valid metadata schema. Attribute 'title' has no value for {}".format(k)
                                    self.add_error('mi_json_schema', msg)
                                    break
                                if v['type'] == 'array':
                                    # we need format attribute set to 'table' in order for the jsoneditor to allow
                                    # editing array type field
                                    if 'format' not in v:
                                        msg = "Not a valid metadata schema. Attribute 'format' is missing for {}"
                                        msg = msg.format(k)
                                        self.add_error('mi_json_schema', msg)
                                        break
                                    elif v['format'] != 'table':
                                        msg = "Not a valid metadata schema. Attribute 'format' should be set " \
                                              "to table for {}"
                                        msg = msg.format(k)
                                        self.add_error('mi_json_schema', msg)
                                        break
                            if 'type' in v and v['type'] == 'object':
                                # we requiring "additionalProperties": false so that we don't allow user to add new
                                # form fields using the jsoneditor form
                                if 'additionalProperties' not in v:
                                    msg = "Not a valid metadata schema. Attribute 'additionalProperties' is " \
                                          "missing for {}"
                                    msg = msg.format(k)
                                    self.add_error('mi_json_schema', msg)
                                    break
                                elif v['additionalProperties']:
                                    msg = "Not a valid metadata schema. Attribute 'additionalProperties' must " \
                                          "be set to false for {}"
                                    msg = msg.format(k)
                                    self.add_error('mi_json_schema', msg)
                                    break

                            # check for nested objects - we are not allowing nested objects to keep the form
                            # generated from the schema by jsoneditor to not get complicated/broken
                            nested_object_found = False
                            for k_child, v_child in v.items():
                                if isinstance(v_child, dict):
                                    if 'type' in v_child and v_child['type'] == 'object':
                                        msg = "Not a valid metadata schema. Nested objects are not allowed. " \
                                              "Attribute '{}' contains nested object"
                                        msg = msg.format(k_child)
                                        self.add_error('mi_json_schema', msg)
                                        nested_object_found = True
                                        break
                            if not nested_object_found:
                                validate_schema(v)
                if is_schema_valid:
                    validate_schema(json_schema['properties'])

        return json_schema

    def update_metadata(self, metadata):
        metadata.version = self.cleaned_data['version']
        metadata.website = self.cleaned_data['website']
        metadata.code_repository = self.cleaned_data['code_repository']
        metadata.release_date = self.cleaned_data['release_date']
        metadata.operating_systems = self.cleaned_data['operating_systems']
        metadata.programming_languages = self.cleaned_data['programming_languages']
        metadata.is_dirty = True
        metadata.save()
        logical_file = metadata.logical_file
        logical_file.mi_schema_json = self.cleaned_data['mi_json_schema']
        logical_file.model_program_type = self.cleaned_data['mp_program_type']
        logical_file.save()
        # recreate ModelProgramResourceFileType objects
        if self.cleaned_data["mp_file_types"]:
            mp_file_types_dict = self.cleaned_data["mp_file_types"]
            # delete all existing ModelProgramResourceFileType objects for this aggregation
            metadata.mp_file_types.all().delete()
            logical_file = metadata.logical_file
            for res_file in logical_file.files.all():
                if res_file.short_path in mp_file_types_dict:
                    mp_file_type = mp_file_types_dict[res_file.short_path]
                    # if mp_file_type is None it means user has removed model file type assignment for the res_file
                    if mp_file_type is not None:
                        ModelProgramResourceFileType.objects.create(file_type=mp_file_type, res_file=res_file,
                                                                    mp_metadata=metadata)
