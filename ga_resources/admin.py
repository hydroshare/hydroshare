from mezzanine.pages.admin import PageAdmin
from ga_resources.models import *
from django.forms import ModelForm
from django import forms

class RenderedLayerAdminForm(ModelForm):
   data_resource = forms.ModelChoiceField(queryset=DataResource.objects.order_by('slug'))
   default_style = forms.ModelChoiceField(queryset=Style.objects.order_by('slug'))
   styles = forms.ModelMultipleChoiceField(queryset=Style.objects.order_by('slug'))

   class Meta:
      model = RenderedLayer
      fields = ['data_resource', 'default_style', 'default_class', 'styles', 'public', 'owner']

class RenderedLayerAdmin(PageAdmin):
   form = RenderedLayerAdminForm
