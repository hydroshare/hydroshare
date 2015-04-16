from django.forms import ModelForm, Textarea, BaseFormSet
from django import forms
from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from hs_app_netCDF.models import *
from hs_core.forms import BaseFormHelper, MetaDataElementDeleteForm
from django.forms.models import formset_factory
from functools import partial, wraps
import copy


# Define form for original coverage
class OriginalCoverageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # The layout below orders how each filed from the Form will be displayed in the frontend
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('name', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('units', css_class=field_width),
                        Field('projection', css_class=field_width),
                        Field('projection_string_type', css_class=field_width),
                        Field('projection_string_text', css_class=field_width),

                 )

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class OriginalCoverageForm(forms.Form):
    PRO_STR_TYPES = (
        ('', '---------'),
        ('EPSG Code', 'EPSG Code'),
        ('OGC WKT Projection', 'OGC WKT Projection'),
        ('Proj4 String', 'Proj4 String')
    )

    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    projection = forms.CharField(max_length=100, required=False, label='Coordinate System Defined in Dataset ')
    northlimit = forms.DecimalField(label='North Limit of Spatial Extent', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Limit of Spatial Extent', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Limit of Spatial Extent', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Limit of Spatial Extent', widget=forms.TextInput())
    units = forms.CharField(max_length=50, label='Units of Spatial Extent')
    projection_string_type = forms.ChoiceField(choices=PRO_STR_TYPES, label='Coordinate System Text Representation Type', required=False)
    projection_string_text = forms.CharField(max_length=1000, label='Coordinate System Text Representation Text', required=False, widget=forms.Textarea())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(OriginalCoverageForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageFormHelper(allow_edit, res_short_id, element_id, element_name='originalcoverage')
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit

    @property
    def form_id(self):
        form_id = 'id_original_coverage_%s'% self.number
        return form_id

    @property
    def form_if_button(self):
        form_id = 'id_original_coverage_%s'% self.number
        return "'" + form_id + "'"

    def clean(self):
        super(OriginalCoverageForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False

        # check required element info
        for key in ('northlimit','eastlimit', 'southlimit', 'westlimit', 'units'):
            value = temp_cleaned_data.get(key, None)
            if not value:
                self._errors[key] = ["Info for $s is missing" % key]
                is_form_errors = True
                del self.cleaned_data[key]

        if is_form_errors:
            return self.cleaned_data

        # if required elements info is provided then write the bounding box info as 'value' dict and assign to self.clean_data
        temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
        temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
        temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
        temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])
        temp_cleaned_data['units'] = temp_cleaned_data['units']

        if 'projection' in temp_cleaned_data:
            if len(temp_cleaned_data['projection']) == 0:
                del temp_cleaned_data['projection']

        if 'name' in temp_cleaned_data:
            if len(temp_cleaned_data['name']) == 0:
                del temp_cleaned_data['name']

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
        if 'name' in self.cleaned_data:
            del self.cleaned_data['name']
        if 'units' in self.cleaned_data:
            del self.cleaned_data['units']
        if 'projection' in self.cleaned_data:
            del self.cleaned_data['projection']

        return self.cleaned_data


class OriginalCoverageMetaDelete(MetaDataElementDeleteForm):
    def __init__(self, res_short_id, element_name, element_id, *args, **kwargs):
        super(OriginalCoverageMetaDelete, self).__init__(res_short_id, element_name, element_id, *args, **kwargs)
        self.helper.layout[0] = HTML('<div class="modal fade" id="delete-original-coverage-element-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">')


# The following 3 classes need to have the "field" same as the fields defined in "Variable" table in models.py
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

       # super(VariableFormHelper, self).__init__(allow_edit, res_short_id,  element_id, element_name, layout,  *args, **kwargs)


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
        # if not allow_edit:
        #     for field in self.fields.values():
        #         field.widget.attrs['readonly'] = True
        #         field.widget.attrs['style'] = "background-color:white;"
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
        # widgets = { 'name': forms.TextInput(attrs={'readonly': 'readonly'}),
        #             'unit': forms.TextInput(),
        #             'type': forms.TextInput(),
        #             'shape': forms.TextInput(attrs={'readonly': 'readonly'}),
        #             'descriptive_name': forms.TextInput(),
        #             'method': forms.Textarea(),#TODO row number abstract example
        #             'missing_value': forms.TextInput()}


class VariableValidationForm(forms.Form):
    name = forms.CharField(max_length=20)
    unit = forms.CharField(max_length=100)
    type = forms.CharField(max_length=100)
    shape = forms.CharField(max_length=100)
    descriptive_name = forms.CharField(max_length=100, required=False)
    method = forms.CharField(max_length=300, required=False)
    missing_value = forms.CharField(max_length=50, required=False)

from hs_core.forms import Helper
ModalDialogLayoutAddVariable = Helper.get_element_add_modal_form('Variable', 'add_variable_modal_form')

# ModalDialogLayoutAddVariable = Layout(
#                             HTML('<div class="modal fade" id="add-variable-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
#                                     '<div class="modal-dialog">'
#                                         '<div class="modal-content">'
#                                             '<form action="{{ add_variable_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
#                                             '{% csrf_token %} '
#                                             '<input name="resource-mode" type="hidden" value="edit"/>'
#                                             '<div class="modal-header">'
#                                                 '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
#                                                 '<h4 class="modal-title" id="myModalLabel">Add Variable</h4>'
#                                             '</div>'
#                                             '<div class="modal-body">'
#                                                 '{% csrf_token %}'
#                                                 '<div class="form-group">'
#                                                     '{% load crispy_forms_tags %} '
#                                                     '{% crispy add_variable_modal_form %} '
#                                                 '</div>'
#                                             '</div>'
#                                             '<div class="modal-footer">'
#                                                 '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'
#                                                 '<button type="submit" class="btn btn-primary">Save changes</button>'
#                                             '</div>'
#                                             '</form>'
#                                         '</div>'
#                                     '</div>'
#                                 '</div>'
#                             )
#                         )


VariableLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in variable_formset.forms %} '
                                     '<div class="item form-group"> '
                                     '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                     '{% crispy form %} '
                                    '<div class="row" style="margin-top:10px">'
                                        '<div class="col-md-10">'
                                            '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-variable-element-dialog_{{ form.number }}" value="Delete Variable">'
                                        '</div>' #change
                                        '<div class="col-md-2">'
                                            '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save Changes</button>'  # change
                                        '</div>'
                                    '</div>'
                                    '{% crispy form.delete_modal_form %} '
                                    '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-creator" class="btn btn-success" data-toggle="modal" data-target="#add-variable-dialog">'
                                 '<i class="fa fa-plus"></i>Add another variable</a>'
                                 '</div>'
                            ),
                    )