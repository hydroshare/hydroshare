__author__ = 'pabitra'
from django.forms import ModelForm, Textarea, BaseFormSet
from django import forms
from django.forms.models import inlineformset_factory, formset_factory
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from models import *

class SiteFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(SiteFormHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Site',
                     Field('site_code', css_class=field_width),
                     Field('site_name', css_class=field_width),
                     Field('organization', css_class=field_width),
                     Field('elevation_m', css_class=field_width),
                     Field('elevation_datum', css_class=field_width),
                     Field('site_type', css_class=field_width),
                     ),
        )

class SiteForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        self.helper = SiteFormHelper()

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type']


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

class MethodForm(ModelForm):
    class Meta:
        model = Method

class ProcessingLevelForm(ModelForm):
    class Meta:
        model = ProcessingLevel

class TimeSeriesResultForm(ModelForm):
    class Meta:
        model = TimeSeriesResult