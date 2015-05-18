__author__ = 'tonycastronova'

from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from hs_model_program.models import MpMetadata


# Keep this one unchanged
class BaseFormHelper(FormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, element_layout=None, *args, **kwargs):
        super(BaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            if element_id:
                self.form_tag = True
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % (
                    res_short_id, element_name, element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % (res_short_id, element_name)
                self.form_tag = False
        else:
            self.form_tag = False

        # change the first character to uppercase of the element name
        element_name = element_name.title()

        if res_short_id and element_id:
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
                         element_layout,),
            )


class mp_form_helper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        # for ModelOutput we have only one field includes_output
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
        super(mp_form_helper, self).__init__(res_short_id, element_id, element_name, layout, *args, **kwargs)


class mp_form(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(mp_form, self).__init__(*args, **kwargs)
        self.helper = mp_form_helper(allow_edit, res_short_id, element_id, element_name='mpmetadata')

        # Set the choice lists as the file names in the content model
        filenames = ['       '] + [f.resource_file.name.split('/')[-1] for f in self.files.all()]
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
    software_version = forms.CharField(max_length=255, required=False)
    software_language = forms.CharField(max_length=100, required=False)
    operating_sys = forms.CharField(max_length=255, required=False)
    date_released = forms.DateTimeField(required=False)
    program_website = forms.CharField(max_length=255, required=False)
    software_repo = forms.CharField(max_length=255, required=False)
    release_notes = forms.CharField(max_length=400, required=False)
    user_manual = forms.CharField(max_length=400, required=False)
    theoretical_manual = forms.CharField(max_length=400, required=False)
    source_code = forms.CharField(max_length=400, required=False)
