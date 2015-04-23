__author__ = 'Mohamed'
from django.forms import ModelForm
from django import forms
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper

#SWATmodelParameters element forms
class SWATmodelParametersFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('has_crop_rotation', css_class=field_width),
                        Field('has_title_drainage', css_class=field_width),
                        Field('has_point_source', css_class=field_width),
                        Field('has_fertilizer', css_class=field_width),
                        Field('has_tilage_operation', css_class=field_width),
                        Field('has_inlet_of_draining_watershed', css_class=field_width),
                        Field('has_irrigation_operation', css_class=field_width),
                        Field('has_other_parameters', css_class=field_width),
                 )
        kwargs['element_name_label'] = 'SWAT model used parameters'
        super(SWATmodelParametersFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SWATmodelParametersForm(ModelForm):
    has_crop_rotation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_title_drainage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_point_source = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_fertilizer = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_tilage_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_inlet_of_draining_watershed = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_irrigation_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_other_parameters = forms.CharField(max_length=200)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SWATmodelParametersForm, self).__init__(*args, **kwargs)
        self.helper = SWATmodelParametersFormHelper(allow_edit, res_short_id, element_id, element_name='SWATmodelParameters')
        self.fields['has_crop_rotation'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_title_drainage'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_point_source'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_fertilizer'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_tilage_operation'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_inlet_of_draining_watershed'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_irrigation_operation'].widget.attrs['style'] = "width:auto;margin-top:-5px"



    class Meta:
        model = SWATmodelParameters
        fields = ['has_crop_rotation',
                  'has_title_drainage',
                  'has_point_source',
                  'has_fertilizer',
                  'has_tilage_operation',
                  'has_inlet_of_draining_watershed',
                  'has_irrigation_operation',
                  'has_other_parameters']
        exclude = ['content_object']
        widgets = {'has_other_parameters': forms.TextInput()}

class SWATmodelParametersValidationForm(forms.Form):
    has_crop_rotation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_title_drainage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_point_source = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_fertilizer = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_tilage_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_inlet_of_draining_watershed = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_irrigation_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')))
    has_other_parameters = forms.CharField(max_length=500, required=False)

    def clean_has_crop_rotation(self):
        data = self.cleaned_data['has_crop_rotation']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_title_drainage(self):
        data = self.cleaned_data['has_title_drainage']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_point_source(self):
        data = self.cleaned_data['has_point_source']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_fertilizer(self):
        data = self.cleaned_data['has_fertilizer']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_tilage_operation(self):
        data = self.cleaned_data['has_tilage_operation']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_inlet_of_draining_watershed(self):
        data = self.cleaned_data['has_inlet_of_draining_watershed']
        if data == u'False':
            return False
        else:
            return True
    def clean_has_irrigation_operation(self):
        data = self.cleaned_data['has_irrigation_operation']
        if data == u'False':
            return False
        else:
            return True

