__author__ = 'pabitra'
from django.forms import ModelForm, Textarea, BaseFormSet
from django import forms
from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from models import *


class BaseFormHelper(FormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, element_layout=None,  *args, **kwargs):
        super(BaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            self.form_tag = True
            if element_id:
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % (res_short_id,element_name, element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % (res_short_id, element_name)
        else:
            self.form_tag = False

        # change the first character to uppercase of the element name
        element_name = element_name.title()

        if res_short_id:
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                                     HTML('<div style="margin-top:10px">'),
                                     HTML('<button type="submit" class="btn btn-primary">Save changes</button>'),
                                     HTML('</div>')
                            ),
                         )
        else:
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                            ),
                          )


class SiteFormHelper(BaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('site_code', css_class=field_width),
                        Field('site_name', css_class=field_width),
                        Field('organization', css_class=field_width),
                        Field('elevation_m', css_class=field_width),
                        Field('elevation_datum', css_class=field_width),
                        Field('site_type', css_class=field_width),
                 )

        super(SiteFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SiteForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.helper = SiteFormHelper(res_short_id, element_id, element_name='Site')

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type']
        exclude = ['content_object']


class SiteValidationForm(forms.Form):
    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255)
    elevation_m = forms.IntegerField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)

class VariableFormHelper(BaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('variable_code', css_class=field_width),
                     Field('variable_name', css_class=field_width),
                     Field('variable_type', css_class=field_width),
                     Field('no_data_value', css_class=field_width),
                     Field('variable_definition', css_class=field_width),
                     Field('speciation', css_class=field_width),
                )

        super(VariableFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)


class VariableForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(VariableForm, self).__init__(*args, **kwargs)
        self.helper = VariableFormHelper(res_short_id, element_id, element_name='Variable')

    class Meta:
        model = Variable
        fields = ['variable_code', 'variable_name', 'variable_type', 'no_data_value', 'variable_definition', 'speciation']
        exclude = ['content_object']

class VariableValidationForm(forms.Form):
    variable_code = forms.CharField(max_length=20)
    variable_name = forms.CharField(max_length=100)
    variable_type = forms.CharField(max_length=100)
    no_data_value = forms.IntegerField()
    variable_definition = forms.CharField(max_length=255, required=False)
    speciation = forms.CharField(max_length=255, required=False)


class MethodFormHelper(BaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                         Field('method_code', css_class=field_width),
                         Field('method_name', css_class=field_width),
                         Field('method_type', css_class=field_width),
                         Field('method_description', css_class=field_width),
                         Field('method_link', css_class=field_width),
                         )

        super(MethodFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)


class MethodForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(MethodForm, self).__init__(*args, **kwargs)
        self.helper = MethodFormHelper(res_short_id, element_id, element_name='Method')

    class Meta:
        model = Method
        fields = ['method_code', 'method_name', 'method_type', 'method_description', 'method_link']
        exclude = ['content_object']


class MethodValidationForm(forms.Form):
    method_code = forms.IntegerField()
    method_name = forms.CharField(max_length=200)
    method_type = forms.CharField(max_length=200)
    method_description = forms.CharField(required=False)
    method_link = forms.URLField(required=False)


class ProcessingLevelFormHelper(BaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('processing_level_code', css_class=field_width),
                     Field('definition', css_class=field_width),
                     Field('explanation', css_class=field_width),
                     )

        super(ProcessingLevelFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ProcessingLevelForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(ProcessingLevelForm, self).__init__(*args, **kwargs)
        self.helper = ProcessingLevelFormHelper(res_short_id, element_id, element_name='ProcessingLevel')

    class Meta:
        model = ProcessingLevel
        fields = ['processing_level_code', 'definition', 'explanation']
        exclude = ['content_object']


class ProcessingLevelValidationForm(forms.Form):
    processing_level_code = forms.IntegerField()
    definition = forms.CharField(max_length=200, required=False)
    explanation = forms.CharField(required=False)


class TimeSeriesResultFormHelper(BaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('units_type', css_class=field_width),
                     Field('units_name', css_class=field_width),
                     Field('units_abbreviation', css_class=field_width),
                     Field('status', css_class=field_width),
                     Field('sample_medium', css_class=field_width),
                     Field('value_count', css_class=field_width),
                     Field('aggregation_statistics', css_class=field_width),
                     )

        super(TimeSeriesResultFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)


class TimeSeriesResultForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(TimeSeriesResultForm, self).__init__(*args, **kwargs)
        self.helper = TimeSeriesResultFormHelper(res_short_id, element_id, element_name='TimeSeriesResult')

    class Meta:
        model = TimeSeriesResult
        fields = ['units_type', 'units_name', 'units_abbreviation', 'status', 'sample_medium', 'value_count',
                  'aggregation_statistics']


class TimeSeriesResultValidationForm(forms.Form):
    units_type = forms.CharField(max_length=255)
    units_name = forms.CharField(max_length=255)
    units_abbreviation = forms.CharField(max_length=20)
    status = forms.CharField(max_length=255)
    sample_medium = forms.CharField(max_length=255)
    value_count = forms.IntegerField()
    aggregation_statistics = forms.CharField(max_length=255)