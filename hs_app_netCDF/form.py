from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from hs_app_netCDF.models import *


class VariableForm(forms.Form):
    # Required Fields
    name = forms.CharField(max_length=50)
    unit = forms.CharField(max_length=50)
    type = forms.CharField(max_length=50)
    shape = forms.CharField(max_length=50)
    # Optional Fields
    descriptive_name = forms.CharField()
    method = forms.CharField(max_length=100)
    missing_value = forms.CharField(max_length=100)
    


Variable_Formsets = formset_factory(VariableForm,extra=2)  # connect variable form with variable model
