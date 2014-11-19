__author__ = 'pabitra'
from django.forms import ModelForm, Textarea
from django import forms
from django.forms.models import inlineformset_factory
from models import *

class SiteForm(ModelForm):
    class Meta:
        model = Site


class VariableForm(ModelForm):
    class Meta:
        model = Variable

class MethodForm(ModelForm):
    class Meta:
        model = Method

class ProcessingLevelForm(ModelForm):
    class Meta:
        model = ProcessingLevel

class TimeSeriesResultForm(ModelForm):
    class Meta:
        model = TimeSeriesResult