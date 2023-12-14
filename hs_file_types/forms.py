import copy
import json

from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Fieldset, HTML, Layout
from django import forms
from django.forms import BaseFormSet, ModelForm
from django.forms.models import formset_factory, model_to_dict

from hs_core.forms import BaseFormHelper, get_crispy_form_fields
from .models.model_program import ModelProgramLogicalFile, ModelProgramResourceFileType
from .models.netcdf import Variable
from .models.raster import BandInformation, CellInformation
from .models.timeseries import Method, ProcessingLevel, Site, TimeSeriesResult, UTCOffSet, VariableTimeseries


class ModelInstanceMetadataValidationForm(forms.Form):
    """Validation form for model instance aggregation"""

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
    """Validation form for model program aggregation"""

    version = forms.CharField(required=False, max_length=250)
    release_date = forms.DateField(required=False)
    website = forms.URLField(required=False, max_length=255)
    code_repository = forms.URLField(required=False, max_length=255)
    programming_languages = forms.CharField(required=False)
    operating_systems = forms.CharField(required=False)
    mp_file_types = forms.CharField(required=False)

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
        json_schema, validation_errors = ModelProgramLogicalFile.validate_meta_schema(schema_string)
        if validation_errors:
            err_message = ", ".join(validation_errors)
            self.add_error(field_name, err_message)
        return json_schema


class OriginalCoverageFormHelper(BaseFormHelper):
    """Helper form for netcdf (multi-dimensional) aggregation original coverage metadata display"""

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
    """Form for displaying original coverage metadata of netcdf aggregation"""

    projection = forms.CharField(max_length=100, required=False,
                                 label='Coordinate Reference System')
    northlimit = forms.DecimalField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Extent', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Extent', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Extent', widget=forms.TextInput())
    units = forms.CharField(max_length=100, label='Extent Unit')
    projection_string_type = forms.CharField(max_length=20, label='Coordinate String Type', required=False,
                                             widget=forms.TextInput())
    projection_string_text = forms.CharField(label='Coordinate String',
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
        self.fields['units'].widget.attrs['readonly'] = True
        self.fields['projection'].widget.attrs['readonly'] = True
        self.fields['datum'].widget.attrs['readonly'] = True
        self.fields['projection_string_type'].widget.attrs['readonly'] = True
        self.fields['projection_string_text'].widget.attrs['readonly'] = True
        self.fields['northlimit'].widget.attrs['readonly'] = True
        self.fields['eastlimit'].widget.attrs['readonly'] = True
        self.fields['southlimit'].widget.attrs['readonly'] = True
        self.fields['westlimit'].widget.attrs['readonly'] = True

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
        raise forms.ValidationError("Original coverage can't be updated")


# The following 3 classes need to have the "field" same as the fields defined in
# "Variable" table in models.py
class VariableFormHelper(FormHelper):
    """Helper form for displaying variable metadata for netcdf aggregation"""

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
    """Form for displaying variable metadata for netcdf aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
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
    """Form for validating variable metadata for netcdf aggregation"""

    name = forms.CharField(max_length=1000)
    unit = forms.CharField(max_length=1000)
    type = forms.CharField(max_length=1000)
    shape = forms.CharField(max_length=1000)
    descriptive_name = forms.CharField(max_length=1000, required=False)
    method = forms.CharField(max_length=10000, required=False)
    missing_value = forms.CharField(max_length=1000, required=False)


# Raster aggregation related forms

class OriginalCoverageRasterFormHelper(BaseFormHelper):
    """Helper form for displaying original coverage metadata of raster aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet
        # is the order these fields will be displayed
        file_type = kwargs.pop('file_type', False)
        form_field_names = ['projection', 'datum', 'projection_string', 'units', 'northlimit',
                            'westlimit', 'southlimit', 'eastlimit']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        layout = Layout(*crispy_form_fields)

        super(OriginalCoverageRasterFormHelper, self).__init__(allow_edit, res_short_id,
                                                               element_id, element_name, layout,
                                                               element_name_label='Spatial Reference',
                                                               *args, **kwargs)


class OriginalCoverageSpatialForm(forms.Form):
    """Form for displaying/editing spatial coverage of raster aggregation"""

    projection = forms.CharField(max_length=100, required=False,
                                 label='Coordinate Reference System',
                                 widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    northlimit = forms.DecimalField(label='North Extent',
                                    widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    eastlimit = forms.DecimalField(label='East Extent',
                                   widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    southlimit = forms.DecimalField(label='South Extent',
                                    widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    westlimit = forms.DecimalField(label='West Extent',
                                   widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    units = forms.CharField(max_length=50, label='Coordinate Reference System Unit',
                            widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    projection_string = forms.CharField(required=False, label='Coordinate String',
                                        widget=forms.Textarea(attrs={'readonly': 'readonly'}))
    datum = forms.CharField(max_length=1000, required=False, label='Datum',
                            widget=forms.TextInput(attrs={'readonly': 'readonly'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        file_type = kwargs.pop('file_type', False)
        super(OriginalCoverageSpatialForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageRasterFormHelper(allow_edit, res_short_id, element_id,
                                                       element_name='OriginalCoverageRaster',
                                                       file_type=file_type)
        self.delete_modal_form = None
        self.number = 0
        self.delete_modal_form = None
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in list(self.fields.values()):
                field.widget.attrs['readonly'] = True

    def clean(self):
        # modify the form's cleaned_data dictionary
        super(OriginalCoverageSpatialForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit', 'units'):
            limit_data = temp_cleaned_data.get(limit, None)
            if not limit_data:
                self._errors[limit] = ["Data for %s is missing" % limit]
                is_form_errors = True
                del self.cleaned_data[limit]

        if is_form_errors:
            return self.cleaned_data

        temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
        temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
        temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
        temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])

        if 'projection' in temp_cleaned_data:
            if len(temp_cleaned_data['projection']) == 0:
                del temp_cleaned_data['projection']
        if 'projection_string' in temp_cleaned_data:
            if len(temp_cleaned_data['projection_string']) == 0:
                del temp_cleaned_data['projection_string']
        if 'datum' in temp_cleaned_data:
            if len(temp_cleaned_data['datum']) == 0:
                del temp_cleaned_data['datum']

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
        if 'projection_string' in self.cleaned_data:
            del self.cleaned_data['projection_string']
        if 'datum' in self.cleaned_data:
            del self.cleaned_data['datum']

        return self.cleaned_data


class CellInfoFormHelper(BaseFormHelper):
    """"Helper form form for displaying/editing cell information metadata of raster aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None,
                 element_name=None, *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the
        # order these fields will be displayed
        form_field_names = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellDataType']
        crispy_form_fields = get_crispy_form_fields(form_field_names)
        layout = Layout(*crispy_form_fields)

        super(CellInfoFormHelper, self).__init__(allow_edit, res_short_id,
                                                 element_id, element_name, layout,
                                                 element_name_label='Cell Information',
                                                 *args, **kwargs)


class CellInfoForm(ModelForm):
    """"Form form for displaying/editing cell information metadata of raster aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CellInfoForm, self).__init__(*args, **kwargs)
        self.helper = CellInfoFormHelper(allow_edit, res_short_id,
                                         element_id, element_name='CellInformation')

        if not allow_edit:
            for field in list(self.fields.values()):
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = CellInformation
        fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellDataType']
        exclude = ['content_object']
        widgets = {'rows': forms.TextInput(attrs={'readonly': 'readonly'}),
                   'columns': forms.TextInput(attrs={'readonly': 'readonly'}),
                   'cellSizeXValue': forms.TextInput(attrs={'readonly': 'readonly'}),
                   'cellSizeYValue': forms.TextInput(attrs={'readonly': 'readonly'}),
                   'cellDataType': forms.TextInput(attrs={'readonly': 'readonly'}),
                   }


class CellInfoValidationForm(forms.Form):
    """"Form for validating cell information metadata of raster aggregation"""

    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required=True)
    cellSizeYValue = forms.FloatField(required=True)
    cellDataType = forms.CharField(max_length=50, required=True)


# repeatable element related forms
class BandBaseFormHelper(FormHelper):
    """"Helper form form for displaying/editing band information metadata of raster aggregation"""

    def __init__(self, res_short_id=None, element_id=None, element_name=None,
                 element_layout=None, *args, **kwargs):
        super(BandBaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            if element_id:
                self.form_tag = True
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % \
                                   (res_short_id, element_name, element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % \
                                   (res_short_id, element_name)
                self.form_tag = False
        else:
            self.form_tag = False

        # change the first character to uppercase of the element name
        element_name = element_name.title()

        if res_short_id and element_id:
            self.layout = Layout(
                Fieldset(element_name,
                         element_layout,
                         HTML("""
                                     <div style="margin-top:10px">
                                     <button type="submit" class="btn btn-primary">
                                     Save changes</button>
                                     </div>
                                     """)
                         )
            )
        else:
            self.layout = Layout(
                Fieldset(element_name,
                         element_layout,
                         )
            )


class BandInfoFormHelper(BandBaseFormHelper):
    """"Helper form form for displaying/editing band information metadata of raster aggregation"""

    def __init__(self, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the
        # order these fields will be displayed
        form_field_names = ['name', 'variableName', 'variableUnit', 'noDataValue', 'maximumValue',
                            'minimumValue', 'method', 'comment']
        crispy_form_fields = get_crispy_form_fields(form_field_names)
        layout = Layout(*crispy_form_fields)

        super(BandInfoFormHelper, self).__init__(res_short_id, element_id,
                                                 element_name, layout, *args, **kwargs)


class BandInfoForm(ModelForm):
    """"Form for displaying/editing band information metadata of raster aggregation"""

    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(BandInfoForm, self).__init__(*args, **kwargs)

        self.helper = BandInfoFormHelper(res_short_id, element_id, element_name='Band Information')
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        if res_short_id:
            self.action = "/hsapi/_internal/%s/bandinformation/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in list(self.fields.values()):
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        form_id = 'id_bandinformation_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_bandinformation_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = BandInformation
        fields = ['name', 'variableName', 'variableUnit', 'noDataValue', 'maximumValue',
                  'minimumValue', 'method', 'comment']
        exclude = ['content_object']
        # set the form layout of each field here.
        widgets = {'variableName': forms.TextInput(),
                   'noDataValue': forms.TextInput(),
                   'maximumValue': forms.TextInput(),
                   'minimumValue': forms.TextInput(),
                   'comment': forms.Textarea,
                   'method': forms.Textarea,
                   }


class BandInfoValidationForm(forms.Form):
    """"Form for validating band information metadata of raster aggregation"""

    name = forms.CharField(max_length=50)
    variableName = forms.CharField(max_length=100)
    variableUnit = forms.CharField(max_length=50)
    noDataValue = forms.DecimalField(required=False)
    maximumValue = forms.DecimalField(required=False)
    minimumValue = forms.DecimalField(required=False)
    method = forms.CharField(required=False)
    comment = forms.CharField(required=False)


class BaseBandInfoFormSet(BaseFormSet):
    """"Formset for displaying multiple band information metadata of raster aggregation"""

    def add_fields(self, form, index):
        super(BaseBandInfoFormSet, self).add_fields(form, index)

    def get_metadata_dict(self):
        bands_data = []
        for form in self.forms:
            band_data = {k: v for k, v in list(form.cleaned_data.items())}
            bands_data.append({'BandInformation': band_data})
        return bands_data


BandInfoFormSet = formset_factory(BandInfoForm, formset=BaseBandInfoFormSet, extra=0)

# TODO: check if this is needed
BandInfoLayoutEdit = Layout(HTML("""
{% load crispy_forms_tags %}
     <div class="col-sm-12 pull-left">
         <div id="variables" class="well">
             <div class="row">
                 {% for form in bandinfo_formset.forms %}
                 <div class="col-sm-6 col-xs-12">
                     <form id="{{form.form_id}}" action="{{ form.action }}" method="POST"
                     enctype="multipart/form-data">
                         {% crispy form %}
                         <div class="row" style="margin-top:10px">
                             <div class="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6">
                                 <button type="button" class="btn btn-primary
                                 pull-right btn-form-submit">Save Changes</button>
                             </div>
                         </div>
                     </form>
                 </div>
                 {% endfor %}
             </div>
         </div>
     </div>
"""
                                 )
                            )

# Geofeature aggregation related forms


class OriginalCoverageGeofeatureFormHelper(BaseFormHelper):
    """"Helper form class for original coverage metadata for the geo feature aggregation."""

    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for
        # the FieldSet is the order these fields will be displayed
        file_type = kwargs.pop('file_type', False)
        form_field_names = ['projection_name', 'datum', 'unit', 'projection_string', 'northlimit',
                            'eastlimit', 'southlimit', 'westlimit']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        layout = Layout(*crispy_form_fields)

        super(OriginalCoverageGeofeatureFormHelper, self). \
            __init__(allow_edit, res_short_id, element_id, element_name, layout,
                     element_name_label='Spatial Reference', *args, **kwargs)


class OriginalCoverageGeofeatureForm(forms.Form):
    """"Form for displaying original coverage metadata of geo feature aggregation."""

    projection_string = forms.CharField(required=False, label='Coordinate String',
                                        widget=forms.Textarea())
    projection_name = forms.CharField(max_length=256,
                                      required=False,
                                      label='Coordinate Reference System')
    datum = forms.CharField(max_length=256, required=False, label='Datum')
    unit = forms.CharField(max_length=256, required=False, label='Unit')

    northlimit = forms.FloatField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.FloatField(label='East Extent', widget=forms.TextInput())
    southlimit = forms.FloatField(label='South Extent', widget=forms.TextInput())
    westlimit = forms.FloatField(label='West Extent', widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        file_type = kwargs.pop('file_type', False)
        super(OriginalCoverageGeofeatureForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageGeofeatureFormHelper(allow_edit,
                                                           res_short_id,
                                                           element_id,
                                                           element_name='OriginalCoverage',
                                                           file_type=file_type)
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in list(self.fields.values()):
                field.widget.attrs['readonly'] = True


class OriginalCoverageGeofeatureValidationForm(forms.Form):
    """"Form for validating original coverage metadata of geo feature aggregation"""

    northlimit = forms.FloatField(required=True)
    eastlimit = forms.FloatField(required=True)
    southlimit = forms.FloatField(required=True)
    westlimit = forms.FloatField(required=True)
    projection_string = forms.CharField(required=False)
    projection_name = forms.CharField(max_length=256, required=False)
    datum = forms.CharField(max_length=256, required=False)
    unit = forms.CharField(max_length=256, required=False)


class GeometryInformationFormHelper(BaseFormHelper):
    """"Helper form for displaying geometry information metadata of geo feature aggregation."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None,
                 element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet
        # is the order these fields will be displayed
        file_type = kwargs.pop('file_type', False)
        form_field_names = ['geometryType', 'featureCount']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        layout = Layout(*crispy_form_fields)

        super(GeometryInformationFormHelper, self) \
            .__init__(allow_edit, res_short_id, element_id, element_name,
                      layout, element_name_label='Geometry Information',
                      *args, **kwargs)


class GeometryInformationForm(forms.Form):
    """"Form for displaying geometry information metadata of geo feature aggregation"""

    geometryType = forms.CharField(max_length=128, required=True, label='Geometry Type')
    featureCount = forms.IntegerField(label='Feature Count',
                                      required=True,
                                      widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        file_type = kwargs.pop('file_type', False)
        super(GeometryInformationForm, self).__init__(*args, **kwargs)
        self.helper = GeometryInformationFormHelper(allow_edit,
                                                    res_short_id,
                                                    element_id,
                                                    element_name='GeometryInformation',
                                                    file_type=file_type)
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in list(self.fields.values()):
                field.widget.attrs['readonly'] = True


class GeometryInformationValidationForm(forms.Form):
    """"Form for validating geometry information metadata of geo feature aggregation."""

    featureCount = forms.IntegerField(required=True)
    geometryType = forms.CharField(max_length=128, required=True)


class FieldInformationValidationForm(forms.Form):
    """"Form for validating field information metadata of geo feature aggregation"""

    fieldName = forms.CharField(required=True, max_length=128)
    fieldType = forms.CharField(required=True, max_length=128)
    fieldTypeCode = forms.CharField(required=False, max_length=50)
    fieldWidth = forms.DecimalField(required=False)
    fieldPrecision = forms.DecimalField(required=False)

# Timeseries aggregation related forms


NO_SELECTION_DROPDOWN_OPTION = "-----"


class SiteFormHelper(BaseFormHelper):
    """"Helper form for displaying site metadata of timeseries aggregation."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_site_code_selection=False, *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        file_type = kwargs.pop('file_type', False)
        field_width = 'form-control input-sm'
        common_layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('available_sites', css_class=field_width, type="hidden"),
            Field('site_code', css_class=field_width,
                  id=_get_field_id('site_code', file_type=file_type),
                  title="A brief and unique code that identifies the site at "
                  "which the data were collected (e.g., 'USU-LBR-Mendon' "
                  "or '10109000')."),
            Field('site_name', css_class=field_width,
                  id=_get_field_id('site_name', file_type=file_type),
                  title="A brief but descriptive name for the site (e.g., "
                  "'Little Bear River at Mendon Road near Mendon, Utah')."),
            Field('organization', css_class=field_width,
                  id=_get_field_id('organization', file_type=file_type),),
            Field('elevation_m', css_class=field_width,
                  id=_get_field_id('elevation_m', file_type=file_type),
                  title="The elevation of the site in meters (e.g., 1345)."),

            Field('elevation_datum', css_class=field_width,
                  id=_get_field_id('elevation_datum', file_type=file_type),
                  title="The datum to which the site elevation is referenced "
                  "(e.g., 'NGVD29').\n"
                  "Select 'Other...' to specify a new elevation datum term."),

            Field('site_type', css_class=field_width,
                  id=_get_field_id('site_type', file_type=file_type),
                  title="A controlled vocabulary term that describes the type of "
                  "data collection site (e.g., 'Stream').\n"
                  "Select 'Other...' to specify a new site type term."),
            Field('latitude', css_class=field_width,
                  id=_get_field_id('latitude', file_type=file_type),
                  title="The latitude coordinate of the site location using the "
                  "WGS84 datum (e.g., 43.1111).",
                  data_map_item="latitude"),
            Field('longitude', css_class=field_width,
                  id=_get_field_id('longitude', file_type=file_type),
                  title="The longitude coordinate of the site location using the "
                  "WGS84 datum (e.g., -111.2334).",
                  data_map_item="longitude"),
        )
        layout = _set_form_helper_layout(common_layout=common_layout, element_name="site",
                                         is_show_element_code_selection=show_site_code_selection,
                                         field_css=field_width)

        super(SiteFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                             layout, *args, **kwargs)


class SiteForm(ModelForm):
    """"Form for displaying site metadata of timeseries aggregation"""

    selected_series_id = forms.CharField(max_length=50, required=False)
    site_code_choices = forms.ChoiceField(choices=(), required=False)
    available_sites = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_site_types = list(kwargs.pop('cv_site_types'))
        self.cv_elevation_datums = list(kwargs.pop('cv_elevation_datums'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_sites = kwargs.pop('available_sites', [])
        show_site_code_selection = kwargs.pop('show_site_code_selection', False)
        file_type = kwargs.pop('file_type', False)
        super(SiteForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_site_code_selection = len(available_sites) > 0 and show_site_code_selection
        self.helper = SiteFormHelper(allow_edit, res_short_id, element_id, element_name='Site',
                                     show_site_code_selection=show_site_code_selection,
                                     file_type=file_type)
        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(form=self, elements=available_sites,
                                           element_name="site")
        code_selection_label = "Select any existing sites to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="site_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_sites,
                                               element_code_att_name="site_code",
                                               element_name_att_name="site_name")

    def set_dropdown_widgets(self, site_type=None, elevation_datum=None):
        cv_site_type_choices = _get_cv_dropdown_widget_items(self.cv_site_types, site_type)
        self.fields['site_type'].widget = forms.Select(choices=cv_site_type_choices)

        cv_e_datum_choices = _get_cv_dropdown_widget_items(self.cv_elevation_datums,
                                                           elevation_datum)
        self.fields['elevation_datum'].widget = forms.Select(choices=cv_e_datum_choices)

    @property
    def form_id(self):
        form_id = 'id_site_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type',
                  'site_code_choices', 'latitude', 'longitude']
        exclude = ['content_object']
        widgets = {'elevation_m': forms.TextInput(), 'latitude': forms.TextInput(),
                   'longitude': forms.TextInput()}
        labels = {'latitude': 'WGS84 Latitude*',
                  'longitude': 'WGS84 Longitude*'
                  }


class SiteValidationForm(forms.Form):
    """"Form for validating site metadata of timeseries aggregation."""

    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255, required=False)
    elevation_m = forms.FloatField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    def clean_latitude(self):
        lat = self.cleaned_data['latitude']
        if lat < -90 or lat > 90:
            raise forms.ValidationError("Value for latitude must be in the range of -90 to 90")
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data['longitude']
        if lon < -180 or lon > 180:
            raise forms.ValidationError("Value for longitude must be in the range of -180 to 180")
        return lon

    def clean_elevation_datum(self):
        e_datum = self.cleaned_data['elevation_datum']
        if e_datum == NO_SELECTION_DROPDOWN_OPTION:
            e_datum = ''
        return e_datum

    def clean_site_type(self):
        s_type = self.cleaned_data['site_type']
        if s_type == NO_SELECTION_DROPDOWN_OPTION:
            s_type = ''
        return s_type

    def clean(self):
        cleaned_data = super(SiteValidationForm, self).clean()
        elevation_m = cleaned_data.get('elevation_m', None)
        elevation_datum = cleaned_data.get('elevation_datum', '')
        if elevation_m is not None:
            if len(elevation_datum.strip()) == 0:
                self._errors['elevation_datum'] = ["A value for elevation datum is missing"]

        return self.cleaned_data


class VariableTimeseriesFormHelper(BaseFormHelper):
    """"Helper form for displaying variable metadata of timeseries aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_variable_code_selection=False, *args, **kwargs):
        file_type = kwargs.pop('file_type', False)
        field_width = 'form-control input-sm'
        common_layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('available_variables', css_class=field_width, type="hidden"),
            Field('variable_code', css_class=field_width,
                  id=_get_field_id('variable_code', file_type=file_type),
                  title="A brief and unique code that identifies the measured "
                  "variable (e.g., 'Temp')."),
            Field('variable_name', css_class=field_width,
                  id=_get_field_id('variable_name', file_type=file_type),
                  title="A brief but descriptive name of the variable that was measured "
                  "selected from a controlled vocabulary of variable names "
                  "(e.g., 'Temperature').\n"
                  "Select 'Other...' to specify a new variable name term."),
            Field('variable_type', css_class=field_width,
                  id=_get_field_id('variable_type', file_type=file_type),
                  title="A term selected from a controlled vocabulary that describes the "
                  "type of variable that was measured (e.g., 'Water quality').\n"
                  "Select 'Other...' to specify a new variable type term."),
            Field('no_data_value', css_class=field_width,
                  id=_get_field_id('no_data_value', file_type=file_type),
                  title="A numeric value that is used to represent 'NoData' values "
                  "in the time series (e.g., -9999)."),
            Field('variable_definition', css_class=field_width,
                  id=_get_field_id('variable_definition', file_type=file_type),
                  title="An optional, longer text description of the variable "
                  "(e.g., 'Water temperature')."),
            Field('speciation', css_class=field_width,
                  id=_get_field_id('speciation', file_type=file_type),
                  title="A term describing the chemical speciation of the resulting data "
                  "values. For most continuous time series from environmental "
                  "sensors, this will be 'Not Applicable'.\n"
                  "Select 'Other...' to specify a new speciation term."),
        )

        layout = _set_form_helper_layout(
            common_layout=common_layout, element_name="variable",
            is_show_element_code_selection=show_variable_code_selection,
            field_css=field_width)

        super(VariableTimeseriesFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                           element_name, layout, *args, **kwargs)


class VariableTimeseriesForm(ModelForm):
    """"Form for displaying variable metadata of timeseries aggregation"""

    selected_series_id = forms.CharField(max_length=50, required=False)
    variable_code_choices = forms.ChoiceField(choices=(), required=False)
    available_variables = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_variable_types = list(kwargs.pop('cv_variable_types'))
        self.cv_variable_names = list(kwargs.pop('cv_variable_names'))
        self.cv_speciations = list(kwargs.pop('cv_speciations'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_variables = kwargs.pop('available_variables', [])
        show_variable_code_selection = kwargs.pop('show_variable_code_selection', False)
        file_type = kwargs.pop('file_type', False)
        super(VariableTimeseriesForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_variable_code_selection = len(available_variables) > 0 and show_variable_code_selection
        self.helper = VariableTimeseriesFormHelper(allow_edit, res_short_id, element_id,
                                                   element_name='Variable',
                                                   show_variable_code_selection=show_variable_code_selection,
                                                   file_type=file_type)
        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(form=self, elements=available_variables,
                                           element_name="variable")
        code_selection_label = "Select any existing variables to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="variable_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_variables,
                                               element_code_att_name="variable_code",
                                               element_name_att_name="variable_name")

    def set_dropdown_widgets(self, variable_type=None, variable_name=None, speciation=None):
        cv_var_type_choices = _get_cv_dropdown_widget_items(self.cv_variable_types, variable_type)
        self.fields['variable_type'].widget = forms.Select(choices=cv_var_type_choices)

        cv_var_name_choices = _get_cv_dropdown_widget_items(self.cv_variable_names, variable_name)
        self.fields['variable_name'].widget = forms.Select(choices=cv_var_name_choices)

        cv_speciation_choices = _get_cv_dropdown_widget_items(self.cv_speciations, speciation)
        self.fields['speciation'].widget = forms.Select(choices=cv_speciation_choices)

    @property
    def form_id(self):
        form_id = 'id_variable_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = VariableTimeseries
        fields = ['variable_code', 'variable_name', 'variable_type', 'no_data_value',
                  'variable_definition', 'speciation', 'variable_code_choices']
        exclude = ['content_object']
        widgets = {'no_data_value': forms.TextInput()}


class VariableTimeseriesValidationForm(forms.Form):
    """"Form for validating variable metadata of timeseries aggregation"""

    variable_code = forms.CharField(max_length=50)
    variable_name = forms.CharField(max_length=100)
    variable_type = forms.CharField(max_length=100)
    no_data_value = forms.IntegerField()
    variable_definition = forms.CharField(max_length=255, required=False)
    speciation = forms.CharField(max_length=255, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean_speciation(self):
        spe = self.cleaned_data['speciation']
        if spe == NO_SELECTION_DROPDOWN_OPTION:
            spe = ''
        return spe

    def clean(self):
        cleaned_data = super(VariableTimeseriesValidationForm, self).clean()
        variable_name = cleaned_data.get('variable_name', None)
        variable_type = cleaned_data.get('variable_type', None)
        if variable_name is None or variable_name == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['variable_name'] = ["A value for variable name is missing"]

        if variable_type is None or variable_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['variable_type'] = ["A value for variable type is missing"]

        return self.cleaned_data


class MethodFormHelper(BaseFormHelper):
    """"Helper form for displaying method metadata of timeseries aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_method_code_selection=False, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        file_type = kwargs.pop('file_type', False)
        field_width = 'form-control input-sm'
        common_layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('available_methods', css_class=field_width, type="hidden"),
            Field('method_code', css_class=field_width,
                  id=_get_field_id('method_code', file_type=file_type),
                  title="A brief and unique code that identifies the method used to "
                  "create the observations (e.g., 'Hydrolab')."),
            Field('method_name', css_class=field_width,
                  id=_get_field_id('method_name', file_type=file_type),
                  title="A brief but descriptive name for the method used to create "
                  "the observations (e.g., 'Hydrolab MiniSonde 5')."),
            Field('method_type', css_class=field_width,
                  id=_get_field_id('method_type', file_type=file_type),
                  title="A term selected from a controlled vocabulary to describe the "
                  "type of method used to create the observations. For "
                  "sensor measurements use 'Instrument deployment'.\n"
                  "Select 'Other...' to specify a new method type term."),
            Field('method_description', css_class=field_width,
                  id=_get_field_id('method_description', file_type=file_type),
                  title="A longer text description of the method "
                  "(e.g., 'Water temperature measured using a "
                  "Hydrolab Multiparameter Sonde')."),
            Field('method_link', css_class=field_width,
                  id=_get_field_id('method_link', file_type=file_type),
                  title="A URL link to a website that contains more information "
                  "about or a detailed description of the method "
                  "(e.g., 'http://www.hydrolab.com')."),
        )

        layout = _set_form_helper_layout(common_layout=common_layout, element_name="method",
                                         is_show_element_code_selection=show_method_code_selection,
                                         field_css=field_width)

        super(MethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                               layout, *args, **kwargs)


class MethodForm(ModelForm):
    """"Form for displaying model metadata of timeseries aggregation"""

    selected_series_id = forms.CharField(max_length=50, required=False)
    method_code_choices = forms.ChoiceField(choices=(), required=False)
    available_methods = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_method_types = list(kwargs.pop('cv_method_types'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_methods = kwargs.pop('available_methods', [])
        show_method_code_selection = kwargs.pop('show_method_code_selection', False)
        file_type = kwargs.pop('file_type', False)
        super(MethodForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_method_code_selection = len(available_methods) > 0 and show_method_code_selection
        self.helper = MethodFormHelper(allow_edit, res_short_id, element_id, element_name='Method',
                                       show_method_code_selection=show_method_code_selection,
                                       file_type=file_type)

        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(self, available_methods, "method")
        code_selection_label = "Select any existing methods to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="method_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_methods,
                                               element_code_att_name="method_code",
                                               element_name_att_name="method_name")

    def set_dropdown_widgets(self, current_method_type=None):
        cv_method_type_choices = _get_cv_dropdown_widget_items(self.cv_method_types,
                                                               current_method_type)
        self.fields['method_type'].widget = forms.Select(choices=cv_method_type_choices)

    @property
    def form_id(self):
        form_id = 'id_method_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = Method
        fields = ['method_code', 'method_name', 'method_type', 'method_description',
                  'method_link', 'method_code_choices']
        exclude = ['content_object']
        widgets = {'method_code': forms.TextInput()}


class MethodValidationForm(forms.Form):
    """"Form for validating method metadata of timeseries aggregation"""

    method_code = forms.CharField(max_length=50)
    method_name = forms.CharField(max_length=200)
    method_type = forms.CharField(max_length=200)
    method_description = forms.CharField(required=False)
    method_link = forms.URLField(required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned_data = super(MethodValidationForm, self).clean()
        method_type = cleaned_data.get('method_type', None)
        if method_type is None or method_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['method_type'] = ["A value for method type is missing"]

        return self.cleaned_data


class ProcessingLevelFormHelper(BaseFormHelper):
    """"Helper form for displaying processing level metadata of timeseries aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_processing_level_code_selection=False, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        file_type = kwargs.pop('file_type', False)
        field_width = 'form-control input-sm'
        common_layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('available_processinglevels', css_class=field_width, type="hidden"),
            Field('processing_level_code', css_class=field_width,
                  id=_get_field_id('processing_level_code', file_type=file_type),
                  title="A brief and unique code that identifies the processing level "
                  "of the observations (e.g., 'QC1')."),
            Field('definition', css_class=field_width,
                  id=_get_field_id('definition', file_type=file_type),
                  title="A brief description of the processing level "
                  "(e.g., 'Quality Controlled Data')."),
            Field('explanation', css_class=field_width,
                  id=_get_field_id('explanation', file_type=file_type),
                  title="A longer text description of the processing level that provides "
                  "more detail about how the processing was done "
                  "(e.g., 'Data that have passed quality control processing')."),
        )

        layout = _set_form_helper_layout(
            common_layout=common_layout,
            element_name="processinglevel",
            is_show_element_code_selection=show_processing_level_code_selection,
            field_css=field_width)

        kwargs['element_name_label'] = 'Processing Level'
        super(ProcessingLevelFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout, *args, **kwargs)


class ProcessingLevelForm(ModelForm):
    """"Form for displaying processing level metadata of timeseries aggregation"""

    selected_series_id = forms.CharField(max_length=50, required=False)
    processinglevel_code_choices = forms.ChoiceField(choices=(), required=False)
    available_processinglevels = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_processinglevels = kwargs.pop('available_processinglevels', [])
        show_processing_level_code_selection = kwargs.pop('show_processing_level_code_selection',
                                                          False)
        file_type = kwargs.pop('file_type', False)
        super(ProcessingLevelForm, self).__init__(*args, **kwargs)
        self.helper = ProcessingLevelFormHelper(
            allow_edit, res_short_id, element_id,
            element_name='ProcessingLevel',
            show_processing_level_code_selection=show_processing_level_code_selection,
            file_type=file_type)

        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(self, available_processinglevels, "processinglevel")
        code_selection_label = "Select any existing processing level to use for this series"
        _set_element_code_selection_form_field(form=self,
                                               form_field_name="processinglevel_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id,
                                               elements=available_processinglevels,
                                               element_code_att_name="processing_level_code",
                                               element_name_att_name="definition")

    @property
    def form_id(self):
        form_id = 'id_processinglevel_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = ProcessingLevel
        fields = ['processing_level_code', 'definition', 'explanation',
                  'processinglevel_code_choices']
        exclude = ['content_object']
        widgets = {'processing_level_code': forms.TextInput()}


class ProcessingLevelValidationForm(forms.Form):
    """"Form for validating processing level metadata of timeseries aggregation"""

    processing_level_code = forms.CharField(max_length=50)
    definition = forms.CharField(max_length=200, required=False)
    explanation = forms.CharField(required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)


class TimeSeriesResultFormHelper(BaseFormHelper):
    """"Helper form for displaying timeseries result metadata of timeseries aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        file_type = kwargs.pop('file_type', False)
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('units_type', css_class=field_width,
                  id=_get_field_id('units_type', file_type=file_type),
                  title="A term selected from a controlled vocabulary that describes the "
                  "type of units used for the Time Series result values "
                  "(e.g., 'Temperature').\n"
                  "Select 'Other...' to specify a new units type term."),
            Field('units_name', css_class=field_width,
                  id=_get_field_id('units_name', file_type=file_type),
                  title="A brief, but descriptive name of the units used for the "
                  "Time Series result values (e.g., 'Degrees Celsius')."),
            Field('units_abbreviation', css_class=field_width,
                  id=_get_field_id('units_abbreviation', file_type=file_type),
                  title="A text abbreviation for the units (e.g., 'Deg. C')."),
            Field('status', css_class=field_width,
                  id=_get_field_id('status', file_type=file_type),
                  title="A term selected from a controlled vocabulary to describe the "
                  "status of the time series. Completed datasets use 'Complete'. "
                  "Where data collection is ongoing, use 'Ongoing'.\n"
                  "Select 'Other...' to specify a new status term."),
            Field('sample_medium', css_class=field_width,
                  id=_get_field_id('sample_medium', file_type=file_type),
                  title="A term selected from a controlled vocabulary to specify the "
                  "environmental medium in which the observation was made "
                  "(e.g., 'Liquid aqueous').\n"
                  "Select 'Other...' to specify a new sample medium term."),
            Field('value_count', css_class=field_width,
                  id=_get_field_id('value_count', file_type=file_type),
                  title="The total number of data values in the Time Series "
                  "(e.g., 24205)."),
            Field('aggregation_statistics', css_class=field_width,
                  id=_get_field_id('aggregation_statistics', file_type=file_type),
                  title="An indication of whether the values are 'Continuous' or "
                  "represent recorded values of some statistic aggregated over a "
                  "time interval (e.g., 'Average').\n"
                  "Select 'Other...' to specify a new aggregation statistics term."),
            Field('series_label', css_class=field_width, type="hidden"),
        )
        kwargs['element_name_label'] = 'Time Series Result'
        super(TimeSeriesResultFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout, *args, **kwargs)


class TimeSeriesResultForm(ModelForm):
    """"Form for displaying timeseries result metadata of timeseries aggregation."""

    selected_series_id = forms.CharField(max_length=50, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        self.cv_sample_mediums = list(kwargs.pop('cv_sample_mediums'))
        self.cv_units_types = list(kwargs.pop('cv_units_types'))
        self.cv_aggregation_statistics = list(kwargs.pop('cv_aggregation_statistics'))
        self.cv_statuses = list(kwargs.pop('cv_statuses'))
        file_type = kwargs.pop('file_type', False)
        super(TimeSeriesResultForm, self).__init__(*args, **kwargs)
        self.helper = TimeSeriesResultFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='TimeSeriesResult',
                                                 file_type=file_type)
        self.fields['selected_series_id'].initial = selected_series_id

    def set_dropdown_widgets(self, current_sample_medium=None, current_units_type=None,
                             current_agg_statistics=None, current_status=None):
        cv_sample_medium_choices = _get_cv_dropdown_widget_items(self.cv_sample_mediums,
                                                                 current_sample_medium)
        self.fields['sample_medium'].widget = forms.Select(choices=cv_sample_medium_choices)
        cv_units_type_choices = _get_cv_dropdown_widget_items(self.cv_units_types,
                                                              current_units_type)
        self.fields['units_type'].widget = forms.Select(choices=cv_units_type_choices)
        cv_status_choices = _get_cv_dropdown_widget_items(self.cv_statuses, current_status)
        self.fields['status'].widget = forms.Select(choices=cv_status_choices)
        cv_agg_statistics_choices = _get_cv_dropdown_widget_items(self.cv_aggregation_statistics,
                                                                  current_agg_statistics)
        self.fields['aggregation_statistics'].widget = forms.Select(
            choices=cv_agg_statistics_choices)

    def set_series_label(self, series_label):
        self.fields['series_label'].initial = series_label

    def set_value_count(self, value_count=None):
        if value_count is not None:
            self.fields['value_count'].initial = value_count

    @property
    def form_id(self):
        form_id = 'id_timeseriesresult_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = TimeSeriesResult
        fields = ['units_type', 'units_name', 'units_abbreviation', 'status', 'sample_medium',
                  'value_count', 'aggregation_statistics', 'series_label']
        widgets = {'value_count': forms.TextInput()}
        labels = {'aggregation_statistics': 'Aggregation statistic'}


class TimeSeriesResultValidationForm(forms.Form):
    """"Form for validating timeseries result metadata of timeseries aggregation"""

    units_type = forms.CharField(max_length=255)
    units_name = forms.CharField(max_length=255)
    units_abbreviation = forms.CharField(max_length=20)
    status = forms.CharField(max_length=255, required=False)
    sample_medium = forms.CharField(max_length=255)
    value_count = forms.IntegerField()
    aggregation_statistics = forms.CharField(max_length=255)
    series_label = forms.CharField(max_length=255, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned_data = super(TimeSeriesResultValidationForm, self).clean()
        units_type = cleaned_data.get('units_type', None)
        status = cleaned_data.get('status', None)
        sample_medium = cleaned_data.get('sample_medium', None)
        aggregation_statistics = cleaned_data.get('aggregation_statistics', None)

        if units_type is None or units_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['units_type'] = ["A value for units type is missing"]

        if status == NO_SELECTION_DROPDOWN_OPTION:
            cleaned_data['status'] = ""

        if sample_medium is None or sample_medium == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['sample_medium'] = ["A value for sample medium is missing"]

        if aggregation_statistics is None or aggregation_statistics == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['aggregation_statistics'] = ["A value for aggregation statistic "
                                                      "is missing"]


class UTCOffSetFormHelper(BaseFormHelper):
    """"Helper form for displaying utc offset time metadata of timeseries aggregation"""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        field_width = 'form-control input-sm'
        file_type = kwargs.pop('file_type', False)
        layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('value', css_class=field_width,
                  id=_get_field_id('utcoffset', file_type=file_type),
                  title="The value of the UTCOffset for timestamp values accompanying your "
                        "time series data."),
        )
        kwargs['element_name_label'] = 'UTC Offset*'
        super(UTCOffSetFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                  element_name, layout, *args, **kwargs)


class UTCOffSetForm(ModelForm):
    """"Form for displaying utc offset time metadata of timeseries aggregation."""

    selected_series_id = forms.CharField(max_length=50, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        file_type = kwargs.pop('file_type', False)
        super(UTCOffSetForm, self).__init__(*args, **kwargs)
        self.helper = UTCOffSetFormHelper(allow_edit, res_short_id, element_id,
                                          element_name='UTCOffSet', file_type=file_type)
        self.fields['selected_series_id'].initial = selected_series_id
        if not element_id:
            self.fields['value'].initial = ""

    class Meta:
        model = UTCOffSet
        fields = ['value']
        exclude = ['content_object']
        widgets = {'value': forms.TextInput()}
        labels = {'value': ""}


class UTCOffSetValidationForm(forms.Form):
    """"Form for validating utl offset time metadata of timeseries aggregation"""

    value = forms.FloatField(required=True)


def _get_cv_dropdown_widget_items(dropdown_items, selected_item_name):
    """Timeseries aggregation related form helper function."""

    # filter out the item that needs to shown as the currently selected item
    # in the dropdown list
    dropdown_items = [item for item in dropdown_items if item.name != selected_item_name]

    # sort the cv items
    cv_item_names = [item.name for item in dropdown_items]
    cv_item_names.sort(key=str.lower)

    # create a list of tuples from item names
    cv_items = [(item_name, item_name) for item_name in cv_item_names]

    if selected_item_name is None or len(selected_item_name) == 0:
        selected_item_name = NO_SELECTION_DROPDOWN_OPTION
        cv_items = [(selected_item_name, selected_item_name)] + cv_items
    else:
        cv_items = [(selected_item_name, selected_item_name)] + cv_items + \
                   [(NO_SELECTION_DROPDOWN_OPTION, NO_SELECTION_DROPDOWN_OPTION)]

    cv_item_choices = tuple(cv_items)
    return cv_item_choices


def _set_available_elements_form_field(form, elements, element_name):
    """Timeseries aggregation related form helper function."""

    elements_data = []
    for element in elements:
        element_data = model_to_dict(element, exclude=["object_id", "series_ids", "content_type"])
        elements_data.append(element_data)
    element_data_str = ""
    if len(elements_data) > 0:
        element_data_str = json.dumps(elements_data)
    form_field_name = "available_{}s".format(element_name)
    form.fields[form_field_name].initial = element_data_str


def _set_element_code_selection_form_field(form, form_field_name, form_field_label, element_id,
                                           elements, element_code_att_name, element_name_att_name):
    """Timeseries aggregation related form helper function."""

    element_display_str = "{code_att_name}:{name_att_name}"
    if len(elements) > 0:
        if len(form.initial) > 0:
            element_code_choices = [(getattr(element, element_code_att_name),
                                     element_display_str.format(
                                         code_att_name=str(getattr(element, element_code_att_name)),
                                         name_att_name=getattr(element, element_name_att_name))
                                     ) for element in elements if element.id != element_id]

            element_code_choices = tuple([(form.initial[element_code_att_name],
                                          element_display_str.format(
                code_att_name=str(form.initial[element_code_att_name]),
                name_att_name=form.initial[element_name_att_name]))]
                + element_code_choices + [("----", "----")])

        else:
            element_code_choices = [(getattr(element, element_code_att_name),
                                     element_display_str.format(
                                         code_att_name=str(getattr(element, element_code_att_name)),
                                         name_att_name=getattr(element, element_name_att_name)))
                                    for element in elements]

            element_code_choices = tuple([("----", "----")] + element_code_choices)

        form.fields[form_field_name].widget = forms.Select(
            choices=element_code_choices)
        form.fields[form_field_name].label = form_field_label


def _get_field_id(field_name, file_type=False):
    """Timeseries aggregation related form helper function."""

    if file_type:
        return "id_{}_filetype".format(field_name)
    return "id_{}".format(field_name)


def _set_form_helper_layout(common_layout, element_name, is_show_element_code_selection, field_css):
    """Timeseries aggregation related form helper function."""

    form_field_name = "{}_code_choices".format(element_name)
    if is_show_element_code_selection:
        element_choice_help = "Select '----' for a new {} or any other option to use an " \
            "existing {} for this series".format(element_name, element_name)

        layout = Layout(
            Field(form_field_name, css_class=field_css, title=element_choice_help),
            common_layout,
        )
    else:
        layout = Layout(
            Field(form_field_name, css_class=field_css, type="hidden"),
            common_layout,
        )
    return layout


UpdateSQLiteLayout = Layout(HTML("""
<div id="sql-file-update" class="row"
{% if not cm.can_update_sqlite_file or not cm.metadata.is_dirty %}style="display:none;
  "{% endif %} style="margin-bottom:10px">
    <div class="col-sm-12">
        <div class="alert alert-warning alert-dismissible" role="alert">
            <strong>SQLite file needs to be synced with metadata changes.</strong>
            {% if cm.metadata.series_names %}
                <div>
                <strong><span style="color:red;">NOTE:</span> New resource specific metadata
                elements can't be created after you update the SQLite file.</strong>
                </div>
            {% endif %}
            <input id="can-update-sqlite-file" type="hidden"
            value="{{ cm.can_update_sqlite_file }}">
            <input id="metadata-dirty" type="hidden" value="{{ cm.metadata.is_dirty }}">
            <form action="/timeseries/sqlite/update/{{ cm.short_id }}/" method="post"
            enctype="multipart/form-data">
                {% csrf_token %}
                <input name="resource-mode" type="hidden" value="edit">
                <button id="btn-update-sqlite-file" type="button" class="btn btn-primary">
                Update SQLite File</button>
            </form>
        </div>
    </div>
</div>
"""
                                 )
                            )

SeriesSelectionLayout = Layout(HTML("""
<div id="div-series-selection">
    <div class="col-sm-12">
        <strong>Select a timeseries to see corresponding metadata (Number of
            timeseries: {{ series_ids.items|length }}):</strong>
        <form action="/resource/{{ cm.short_id }}/" method="get" enctype="multipart/form-data">
            {% csrf_token %}
            <input name="resource-mode" type="hidden" value="edit">
            <select class="form-control" name="series_id" id="series_id">
                {% for series_id, label in series_ids.items %}
                    {% if selected_series_id == series_id %}
                        <option value="{{ series_id }}" selected="selected"
                                title="{{ label }}">{{ label|slice:":120"|add:"..." }}</option>
                    {% else %}
                        <option value="{{ series_id }}" title="{{ label }}">
                        {{ label|slice:":120"|add:"..." }}</option>
                    {% endif %}
                {% endfor %}
            </select>
        </form>
        <hr>
    </div>
</div>
"""
                                    )
                               )
UTCOffSetLayout = HTML("""
<div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="utc_offset">
         {% load crispy_forms_tags %}
         {% crispy utcoffset_form %}
         <hr style="border:0">
     </div>
</div>
""")

TimeSeriesMetaDataLayout = HTML("""
<div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="site" class="hs-coordinates-picker" data-coordinates-type="point">
         {% load crispy_forms_tags %}
         {% crispy site_form %}
         <hr style="border:0">
     </div>
     <div id="variable">
         {% load crispy_forms_tags %}
         {% crispy variable_form %}
         <hr style="border:0">
     </div>
     <div id="method">
         {% load crispy_forms_tags %}
         {% crispy method_form %}
         <hr style="border:0">
     </div>
 </div>

 <div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="processinglevel">
         {% load crispy_forms_tags %}
         {% crispy processing_level_form %}
         <hr style="border:0">
     </div>
     <div id="timeseriesresult">
         {% load crispy_forms_tags %}
         {% crispy timeseries_result_form %}
     </div>
 </div>
"""
                                )
