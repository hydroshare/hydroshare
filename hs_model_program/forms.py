__author__ = 'tonycastronova'

from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from hs_model_program.models import MpMetadata
from hs_core.forms import BaseFormHelper

class mp_form_helper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):

        field_width = 'form-control input-sm'
        layout = Layout(
            Field('software_version', css_class=field_width),
            Field('software_language', css_class=field_width),
            Field('software_repo', css_class=field_width),
            Field('operating_sys', css_class=field_width),
            Field('date_released', css_class=field_width),
            Field('program_website', css_class=field_width),
            Field('release_notes', css_class=field_width),
            Field('user_manual', css_class=field_width),
            Field('theoretical_manual', css_class=field_width),
            Field('source_code', css_class=field_width),
        )
        super(mp_form_helper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='  ',  *args, **kwargs)


class mp_form(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        # pop files from kwargs, else metadata will fail to load in edit mode
        files = kwargs.pop('files')
        super(mp_form, self).__init__(*args, **kwargs)
        self.helper = mp_form_helper(allow_edit, res_short_id, element_id, element_name='MpMetadata')


        # Set the choice lists as the file names in the content model
        filenames = ['       '] + [f.resource_file.name.split('/')[-1] for f in files.all()]
        CHOICES = tuple((f, f) for f in filenames)
        self.fields['release_notes'].choices = CHOICES
        self.fields['user_manual'].choices = CHOICES
        self.fields['source_code'].choices = CHOICES
        self.fields['theoretical_manual'].choices = CHOICES

    class Meta:
        model = MpMetadata

        fields = ['software_version',
                  'software_language',
                  'software_repo',
                  'operating_sys',
                  'date_released',
                  'program_website',
                  'release_notes',
                  'user_manual',
                  'theoretical_manual',
                  'source_code']
        exclude = ['content_object']


class mp_form_validation(forms.Form):
    software_version = forms.CharField(required=False)
    software_language = forms.CharField(required=False)
    operating_sys = forms.CharField(required=False)
    date_released = forms.DateTimeField(required=False)
    program_website = forms.CharField(required=False)
    software_repo = forms.CharField(required=False)
    release_notes = forms.CharField(required=False)
    user_manual = forms.CharField(required=False)
    theoretical_manual = forms.CharField(required=False)
    source_code = forms.CharField(required=False)

