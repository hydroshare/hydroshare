import copy

from django.forms import ModelForm
from django import forms

from crispy_forms.layout import Layout, HTML, Fieldset
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import Field

from hs_core.forms import BaseFormHelper, MetaDataElementDeleteForm, Helper, get_crispy_form_fields
from hs_app_netCDF.models import Variable


# Define form for original coverage
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


ModalDialogLayoutAddVariable = Helper.get_element_add_modal_form('Variable',
                                                                 'add_variable_modal_form')

VariableLayoutEdit = Layout(
    HTML(
        """
        {% load crispy_forms_tags %}
        {% if variable_formset.forms %}
            <div class="col-xs-12">
                <div id="variables" class="well">
                    <div class="row">
                        {% for form in variable_formset.forms %}
                            <div class="form-group col-xs-12 col-md-4">
                                <form id={{ form.form_id }} action="{{ form.action }}"
                                      method="POST" enctype="multipart/form-data">
                                    {% crispy form %}
                                    <div class="row" style="margin-top:10px">
                                        <div class="col-md-10 col-xs-6">
                                            <button type="button"
                                                class="btn btn-primary btn-form-submit">
                                                Save Changes
                                            </button>
                                        </div>
                                    </div>
                                    {% crispy form.delete_modal_form %}
                                </form>
                            </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
        {% endif %}
        """
        ))
