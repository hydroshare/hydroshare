
from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from hs_model_program.models import MpMetadata

class mp_form(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(mp_form, self).__init__(*args, **kwargs)

    class Meta:
        model = MpMetadata
        fields = []

class mp_form_validation(forms.Form):
    modelVersion = forms.CharField(required=False)
    modelProgramLanguage = forms.CharField(required=False)
    modelOperatingSystem = forms.CharField(required=False)
    modelReleaseDate = forms.DateTimeField(required=False)
    modelWebsite = forms.CharField(required=False)
    modelCodeRepository = forms.CharField(required=False)
    modelReleaseNotes = forms.CharField(required=False)
    modelDocumentation = forms.CharField(required=False)
    modelSoftware = forms.CharField(required=False)
    modelEngine = forms.CharField(required=False)