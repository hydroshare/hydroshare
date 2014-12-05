__author__ = 'pabitra'
from django.forms import ModelForm, Textarea, BaseFormSet
from django import forms
from django.forms.models import inlineformset_factory, formset_factory
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from models import *

class SiteFormHelper(FormHelper):
    def __init__(self, res_short_id=None, element_id=None,  *args, **kwargs):
        super(SiteFormHelper, self).__init__(*args, **kwargs)
        if res_short_id:
            self.form_method = 'post'
            self.form_tag = True
            if element_id:
                self.form_action = "/hsapi/_internal/%s/site/%s/update-metadata/" % (res_short_id, element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/site/add-metadata/" % res_short_id
        else:
            self.form_tag = False
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

        if res_short_id:
            self.layout = Layout(
                            Fieldset('Site',
                                     layout,
                                     HTML('<button type="submit" class="btn btn-primary">Save changes</button>'),
                            ),
                         )
        else:
            self.layout = Layout(
                            Fieldset('Site',
                                     layout,
                            ),
                          )

class SiteForm(ModelForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.helper = SiteFormHelper(res_short_id, element_id)

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type']
        exclude = ['content_object']


class SiteTestForm(forms.Form):
    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255)
    elevation_m = forms.IntegerField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)

class VariableFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(VariableFormHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Variable',
                     Field('variable_code', css_class=field_width),
                     Field('variable_name', css_class=field_width),
                     Field('variable_type', css_class=field_width),
                     Field('no_data_value', css_class=field_width),
                     Field('variable_definition', css_class=field_width),
                     Field('speciation', css_class=field_width),
                     ),
        )

class VariableForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(VariableForm, self).__init__(*args, **kwargs)
        self.helper = VariableFormHelper()

    class Meta:
        model = Variable
        fields = ['variable_code', 'variable_name', 'variable_type', 'no_data_value', 'variable_definition', 'speciation']


class MethodFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(MethodFormHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Method',
                     Field('method_code', css_class=field_width),
                     Field('method_name', css_class=field_width),
                     Field('method_type', css_class=field_width),
                     Field('method_description', css_class=field_width),
                     Field('method_link', css_class=field_width),
                     ),
        )


class MethodForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(MethodForm, self).__init__(*args, **kwargs)
        self.helper = MethodFormHelper()

    class Meta:
        model = Method
        fields = ['method_code', 'method_name', 'method_type', 'method_description', 'method_link']



class ProcessingLevelFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ProcessingLevelFormHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Processing Level',
                     Field('processing_level_code', css_class=field_width),
                     Field('definition', css_class=field_width),
                     Field('explanation', css_class=field_width),
                     ),
        )


class ProcessingLevelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProcessingLevelForm, self).__init__(*args, **kwargs)
        self.helper = ProcessingLevelFormHelper()

    class Meta:
        model = ProcessingLevel
        fields = ['processing_level_code', 'definition', 'explanation']


class TimeSeriesResultFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(TimeSeriesResultFormHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Timeseries Result',
                     Field('units_type', css_class=field_width),
                     Field('units_name', css_class=field_width),
                     Field('units_abbreviation', css_class=field_width),
                     Field('status', css_class=field_width),
                     Field('sample_medium', css_class=field_width),
                     Field('value_count', css_class=field_width),
                     Field('aggregation_statistics', css_class=field_width),
                     ),
        )


class TimeSeriesResultForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(TimeSeriesResultForm, self).__init__(*args, **kwargs)
        self.helper = TimeSeriesResultFormHelper()

    class Meta:
        model = TimeSeriesResult
        fields = ['units_type', 'units_name', 'units_abbreviation', 'status', 'sample_medium', 'value_count',
                  'aggregation_statistics']