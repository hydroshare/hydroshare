import copy
import json

import jsonschema
from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, HTML, Fieldset
from django import forms
from django.forms import ModelForm

from hs_core.forms import BaseFormHelper, MetaDataElementDeleteForm, get_crispy_form_fields
from .models.model_program import ModelProgramResourceFileType
from .models.netcdf import Variable


class ModelInstanceMetadataValidationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.resource = kwargs.pop('resource')
        super(ModelInstanceMetadataValidationForm, self).__init__(*args, **kwargs)

    has_model_output = forms.BooleanField(required=False)
    executed_by = forms.IntegerField(required=False)
    user_selected_mp_aggr = None

    def clean_executed_by(self):
        executed_by = self.cleaned_data['executed_by']
        selected_mp_aggr = None
        # if a model program has been selected then this form would have the id of that aggregation
        if executed_by is not None and executed_by > 0:
            mp_aggregations = self.resource.modelprogramlogicalfile_set.all()
            for mp_aggr in mp_aggregations:
                if mp_aggr.id == executed_by:
                    selected_mp_aggr = mp_aggr
                    self.user_selected_mp_aggr = selected_mp_aggr
                    break
            else:
                self.add_error("executed_by", "Selected model program aggregation must be from the same resource")
        return selected_mp_aggr

    def update_metadata(self, metadata):
        executed_by = self.cleaned_data['executed_by']
        if executed_by:
            metadata.executed_by = executed_by
            logical_file = metadata.logical_file
            if not logical_file.metadata_schema_json or not metadata.metadata_json:
                logical_file.metadata_schema_json = self.user_selected_mp_aggr.metadata_schema_json
                logical_file.save()
        else:
            metadata.executed_by = None

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
    mp_file_types = forms.CharField(required=False)
    mp_program_type = forms.CharField(max_length=255)
    # allow user to upload a json schema file
    mi_json_schema_file = forms.FileField(required=False)
    # allow user to select one of the existing schema templates
    mi_json_schema_template = forms.CharField(max_length=255, required=False)

    def clean_version(self):
        version = self.cleaned_data['version'].strip()
        return version

    def clean_programming_languages(self):
        language_string = self.cleaned_data['programming_languages'].strip()
        if language_string:
            # generate a list of strings
            languages = language_string.split(',')
            languages = [lang.strip() for lang in languages]
            return languages
        return []

    def clean_operating_systems(self):
        os_string = self.cleaned_data['operating_systems'].strip()
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
                # format of 'mp_file_type_string' is as 'resource file short path':'mp file type name'
                mp_file_type_lst = mp_file_type_string.split(":")
                if len(mp_file_type_lst) != 2:
                    err_msg = "Input data format ({}) for model program file type " \
                              "is invalid".format(mp_file_type_string)
                    self.add_error("mp_file_types", err_msg)
                if mp_file_type_lst[1].lower() != "none":
                    mp_file_type = ModelProgramResourceFileType.type_from_string(mp_file_type_lst[1].lower())
                    if mp_file_type is None:
                        err_msg = "{} not a valid model program file type".format(mp_file_type_lst[1])
                        self.add_error("mp_file_types", err_msg)

                    mp_file_types_dict[mp_file_type_lst[0]] = mp_file_type_lst[1]
                else:
                    mp_file_types_dict[mp_file_type_lst[0]] = None
        return mp_file_types_dict

    def clean_mi_json_schema_file(self):
        json_schema = dict()
        json_schema_file = self.cleaned_data['mi_json_schema_file']
        if json_schema_file:
            schema_data = json_schema_file.read().decode("utf-8")
            if schema_data:
                return self._validate_json_schema(schema_string=schema_data, field_name='mi_json_schema_file')
        return json_schema

    def clean_mi_json_schema_template(self):
        json_schema = dict()
        json_schema_template_path = self.cleaned_data['mi_json_schema_template']
        if json_schema_template_path:
            with open(json_schema_template_path) as file_obj:
                schema_data = file_obj.read()
                json_schema = json.loads(schema_data)

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

        # check for user uploaded schema json file or selected schema template
        # we will use the content of that file/template to populate the the metadata_schema_json metadata field
        if self.cleaned_data['mi_json_schema_template']:
            # use the content from the selected schema template file to save in database
            logical_file.metadata_schema_json = self.cleaned_data['mi_json_schema_template']
        elif self.cleaned_data['mi_json_schema_file']:
            # use the content from the uploaded json file to save in database
            logical_file.metadata_schema_json = self.cleaned_data['mi_json_schema_file']

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
                        ModelProgramResourceFileType.create(file_type=mp_file_type, res_file=res_file,
                                                            mp_metadata=metadata)

    def _validate_json_schema(self, schema_string, field_name):
        """helper to validate json schema for model instance metadata
        :param  schema_string: metadata json schema as a string - which needs to be validated
        :param  field_name: form field name for which the json schema input is getting validated
        :returns   a dict object containing the validated json schema
        """
        json_schema = dict()
        is_schema_valid = True
        try:
            json_schema = json.loads(schema_string)
        except ValueError:
            self.add_error(field_name, "Schema is not valid JSON")
            return json_schema

        if json_schema:
            schema_version = json_schema.get("$schema", "")
            if not schema_version:
                is_schema_valid = False
                err_message = "Not a valid JSON schema. {}"
                if "$schema" not in json_schema:
                    err_message = err_message.format("Key '$schema' is missing")
                else:
                    err_message = err_message.format("Key '$schema' is missing a value for schema version")
                self.add_error(field_name, err_message)
            else:
                if "/draft-04/" not in schema_version:
                    is_schema_valid = False
                    err_message = "Not a valid JSON schema. Schema version is invalid. Supported valid version(s): " \
                                  "draft-04"
                    self.add_error(field_name, err_message)

            if 'properties' not in json_schema:
                is_schema_valid = False
                self.add_error(field_name,
                               "Not a valid metadata schema. Attribute 'properties' "
                               "is missing")

            if is_schema_valid:
                try:
                    jsonschema.Draft4Validator.check_schema(json_schema)
                except jsonschema.SchemaError as ex:
                    is_schema_valid = False
                    schema_err_msg = "{}. Schema invalid field path:{}".format(ex.message, str(list(ex.path)))
                    self.add_error(field_name, "Not a valid JSON schema. Error:{}".format(schema_err_msg))

        if is_schema_valid:
            # custom validation - hydroshare requirements
            # this custom validation requiring additional attributes are needed for making the json-editor form
            # generation at the front-end to work
            if 'additionalProperties' not in json_schema:
                is_schema_valid = False
                self.add_error(field_name,
                               "Not a valid metadata schema. Attribute 'additionalProperties' "
                               "is missing")
            elif json_schema['additionalProperties']:
                is_schema_valid = False
                self.add_error(field_name,
                               "Not a valid metadata schema. Attribute 'additionalProperties' "
                               "should bet set to 'false'")

            def validate_schema(schema_dict):
                for k, v in schema_dict.items():
                    # key must not have whitespaces - required for xml encoding of metadata
                    if k != k.strip():
                        msg = "Not a valid metadata schema. Attribute '{}' has leading or trailing whitespaces"
                        msg = msg.format(k)
                        self.add_error(field_name, msg)
                    # key must consists of alphanumeric characters only - required for xml encoding of metadata
                    if not k.isalnum():
                        msg = "Not a valid metadata schema. Attribute '{}' has non-alphanumeric characters"
                        msg = msg.format(k)
                        self.add_error(field_name, msg)
                    # key must start with a alphabet character - required for xml encoding of metadata
                    if not k[0].isalpha():
                        msg = "Not a valid metadata schema. Attribute '{}' starts with a non-alphabet character"
                        msg = msg.format(k)
                        self.add_error(field_name, msg)

                    if isinstance(v, dict):
                        if k not in ('properties', 'items'):
                            # we need a title to use as label for the form field
                            if 'title' not in v:
                                msg = "Not a valid metadata schema. Attribute 'title' is missing for {}".format(k)
                                self.add_error(field_name, msg)
                            elif len(v['title'].strip()) == 0:
                                msg = "Not a valid metadata schema. Attribute 'title' has no value for {}".format(k)
                                self.add_error(field_name, msg)
                            if v['type'] == 'array':
                                # we need format attribute set to 'table' in order for the jsoneditor to allow
                                # editing array type field
                                if 'format' not in v:
                                    msg = "Not a valid metadata schema. Attribute 'format' is missing for {}"
                                    msg = msg.format(k)
                                    self.add_error(field_name, msg)
                                elif v['format'] != 'table':
                                    msg = "Not a valid metadata schema. Attribute 'format' should be set " \
                                          "to table for {}"
                                    msg = msg.format(k)
                                    self.add_error(field_name, msg)
                        if 'type' in v and v['type'] == 'object':
                            # we requiring "additionalProperties": false so that we don't allow user to add new
                            # form fields using the json-editor form
                            if 'additionalProperties' not in v:
                                msg = "Not a valid metadata schema. Attribute 'additionalProperties' is " \
                                      "missing for {}"
                                msg = msg.format(k)
                                self.add_error(field_name, msg)
                            elif v['additionalProperties']:
                                msg = "Not a valid metadata schema. Attribute 'additionalProperties' must " \
                                      "be set to false for {}"
                                msg = msg.format(k)
                                self.add_error(field_name, msg)

                        # check for nested objects - we are not allowing nested objects to keep the form
                        # generated from the schema by json-editor to not get complicated
                        nested_object_found = False
                        if 'type' in v and v['type'] == 'object':
                            # parent type is object - check child type is not object
                            for k_child, v_child in v.items():
                                if isinstance(v_child, dict):
                                    if 'type' in v_child and v_child['type'] == 'object':
                                        msg = "Not a valid metadata schema. Nested object types are not allowed. " \
                                              "Attribute '{}' contains nested object types"
                                        msg = msg.format(k_child)
                                        self.add_error(field_name, msg)
                                        nested_object_found = True
                        if not nested_object_found:
                            validate_schema(v)

            if is_schema_valid:
                validate_schema(json_schema['properties'])

        return json_schema


class OriginalCoverageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):

        # The layout below orders how each filed from the Form will be displayed in the frontend
        file_type = kwargs.pop('file_type', False)
        form_field_names = ['projection', 'datum', 'projection_string_type',
                            'projection_string_text', 'units', 'northlimit', 'eastlimit',
                            'southlimit', 'westlimit']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        layout = Layout(*crispy_form_fields)

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout,
                                                         element_name_label='Spatial Reference',
                                                         *args, **kwargs)


class OriginalCoverageForm(forms.Form):
    PRO_STR_TYPES = (
        ('', '---------'),
        ('WKT String', 'WKT String'),
        ('Proj4 String', 'Proj4 String')
    )

    projection = forms.CharField(max_length=100, required=False,
                                 label='Coordinate Reference System')
    northlimit = forms.DecimalField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Extent', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Extent', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Extent', widget=forms.TextInput())
    units = forms.CharField(max_length=100, label='Extent Unit')
    projection_string_type = forms.ChoiceField(choices=PRO_STR_TYPES,
                                               label='Coordinate String Type', required=False)
    projection_string_text = forms.CharField(max_length=1000, label='Coordinate String',
                                             required=False, widget=forms.Textarea())
    datum = forms.CharField(max_length=300, label='Datum', required=False, widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        file_type = kwargs.pop('file_type', False)
        super(OriginalCoverageForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='originalcoverage',
                                                 file_type=file_type)
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        self.fields['projection'].widget.attrs['readonly'] = True
        self.fields['datum'].widget.attrs['readonly'] = True
        self.fields['projection_string_type'].widget.attrs['readonly'] = True
        self.fields['projection_string_text'].widget.attrs['readonly'] = True
        # add the 'data-map-item' attribute so that map interface can be used for
        # editing these fields
        self.fields['northlimit'].widget.attrs['data-map-item'] = 'northlimit'
        self.fields['eastlimit'].widget.attrs['data-map-item'] = 'eastlimit'
        self.fields['southlimit'].widget.attrs['data-map-item'] = 'southlimit'
        self.fields['westlimit'].widget.attrs['data-map-item'] = 'westlimit'

    @property
    def form_id(self):
        form_id = 'id_original_coverage_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_original_coverage_%s' % self.number
        return "'" + form_id + "'"

    def clean(self):
        super(OriginalCoverageForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False

        # check required element info
        for key in ('northlimit', 'eastlimit', 'southlimit', 'westlimit', 'units'):
            value = temp_cleaned_data.get(key, None)
            if not value:
                self._errors[key] = ["Info for %s is missing" % key]
                is_form_errors = True
                del self.cleaned_data[key]

        if is_form_errors:
            return self.cleaned_data

        # if required elements info is provided then write the bounding box info
        # as 'value' dict and assign to self.clean_data
        temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
        temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
        temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
        temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])
        temp_cleaned_data['units'] = temp_cleaned_data['units']

        if 'projection' in temp_cleaned_data:
            if len(temp_cleaned_data['projection']) == 0:
                del temp_cleaned_data['projection']

        if 'projection_string_type' in temp_cleaned_data:
            del temp_cleaned_data['projection_string_type']

        if 'projection_string_text' in temp_cleaned_data:
            del temp_cleaned_data['projection_string_text']

        self.cleaned_data['value'] = copy.deepcopy(temp_cleaned_data)

        if 'northlimit' in self.cleaned_data:
                del self.cleaned_data['northlimit']
        if 'eastlimit' in self.cleaned_data:
                del self.cleaned_data['eastlimit']
        if 'southlimit' in self.cleaned_data:
            del self.cleaned_data['southlimit']
        if 'westlimit' in self.cleaned_data:
            del self.cleaned_data['westlimit']
        if 'units' in self.cleaned_data:
            del self.cleaned_data['units']
        if 'projection' in self.cleaned_data:
            del self.cleaned_data['projection']

        return self.cleaned_data


class OriginalCoverageValidationForm(forms.Form):
    PRO_STR_TYPES = (
        ('', '---------'),
        ('WKT String', 'WKT String'),
        ('Proj4 String', 'Proj4 String')
    )

    projection = forms.CharField(max_length=100, required=False)
    northlimit = forms.DecimalField()
    eastlimit = forms.DecimalField()
    southlimit = forms.DecimalField()
    westlimit = forms.DecimalField()
    units = forms.CharField(max_length=100)
    projection_string_type = forms.ChoiceField(choices=PRO_STR_TYPES, required=False)
    projection_string_text = forms.CharField(max_length=1000, required=False)
    datum = forms.CharField(max_length=300, required=False)


class OriginalCoverageMetaDelete(MetaDataElementDeleteForm):
    def __init__(self, res_short_id, element_name, element_id, *args, **kwargs):
        super(OriginalCoverageMetaDelete, self).__init__(res_short_id, element_name,
                                                         element_id, *args, **kwargs)
        self.helper.layout[0] = HTML("""
            <div class="modal fade" id="delete-original-coverage-element-dialog"
            tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">
        """)


# The following 3 classes need to have the "field" same as the fields defined in
# "Variable" table in models.py
class VariableFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(VariableFormHelper, self).__init__(*args, **kwargs)
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = True
        # change the fields name here
        self.layout = Layout(
            Fieldset('Variable',
                     Field('name', css_class=field_width),
                     Field('unit', css_class=field_width),
                     Field('type', css_class=field_width),
                     Field('shape', css_class=field_width),
                     Field('descriptive_name', css_class=field_width),
                     Field('method', css_class=field_width),
                     Field('missing_value', css_class=field_width)
                     ),
            )


class VariableForm(ModelForm):

    def __init__(self, allow_edit=True, res_short_id=None,  *args, **kwargs):
        super(VariableForm, self).__init__(*args, **kwargs)
        self.helper = VariableFormHelper()
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        if res_short_id:
            self.action = "/hsapi/_internal/%s/variable/add-metadata/" % res_short_id
        else:
            self.action = ""
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['shape'].widget.attrs['readonly'] = True
        self.fields['type'].widget.attrs['readonly'] = True

    @property
    def form_id(self):
        form_id = 'id_variable_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_variable_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Variable
        # change the fields same here
        fields = ['name', 'unit', 'type', 'shape', 'descriptive_name', 'method', 'missing_value']
        exclude = ['content_object']


class VariableValidationForm(forms.Form):
    name = forms.CharField(max_length=1000)
    unit = forms.CharField(max_length=1000)
    type = forms.CharField(max_length=1000)
    shape = forms.CharField(max_length=1000)
    descriptive_name = forms.CharField(max_length=1000, required=False)
    method = forms.CharField(max_length=10000, required=False)
    missing_value = forms.CharField(max_length=1000, required=False)
