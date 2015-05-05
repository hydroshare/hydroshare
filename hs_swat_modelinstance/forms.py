__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper

#SWATmodelParameters element forms
class ModelObjectiveFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('swat_model_objective', css_class=field_width),
                        Field('other_objectives', css_class=field_width),
                 )
        kwargs['element_name_label'] = 'Model objective'
        super(ModelObjectiveFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelObjectiveForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        objective_choices = tuple([('Choose an objective', 'Choose an objective'), ('Hydrology', 'Hydrology'),\
                                   ('Water quality', 'Water quality'), ('BMPs', 'BMPs'),\
                                   ('Climate / Landuse Change', 'Climate / Landuse Change'), ('Other', 'Other')])
        super(ModelObjectiveForm, self).__init__(*args, **kwargs)
        self.helper = ModelObjectiveFormHelper(allow_edit, res_short_id, element_id, element_name='ModelObjective')
        self.fields['swat_model_objective'].choices = objective_choices

    class Meta:
        model = ModelObjective
        fields = ['swat_model_objective',
                  'other_objectives']
        exclude = ['content_object']


class ModelObjectiveValidationForm(forms.Form):
    swat_model_objective = forms.CharField(max_length=100, required=False)
    other_objectives = forms.CharField(max_length=500, required=False)

class simulationTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('simulation_type_name', css_class=field_width),
                 )
        kwargs['element_name_label'] = 'Simulation type'
        super(simulationTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class simulationTypeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        type_choices = tuple([('Choose a type', 'Choose a type'),\
                                   ('Normal Simulation', 'Normal Simulation'),\
                                   ('Sensitivity Analysis', 'Sensitivity Analysis'),\
                                   ('Auto-Calibration', 'Auto-Calibration')])
        super(simulationTypeForm, self).__init__(*args, **kwargs)
        self.helper = simulationTypeFormHelper(allow_edit, res_short_id, element_id, element_name='simulationType')
        self.fields['simulation_type_name'].choices = type_choices

    class Meta:
        model = simulationType
        fields = ['simulation_type_name']
        exclude = ['content_object']


class simulationTypeValidationForm(forms.Form):
    simulation_type_name = forms.CharField(max_length=100, required=False)

class ModelMethodsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('runoff_calculation_method', css_class=field_width),
                        Field('flow_routing_method', css_class=field_width),
                        Field('PET_estimation_method', css_class=field_width),
                 )
        kwargs['element_name_label'] = 'Model Methods'
        super(ModelMethodsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelMethodsForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelMethodsForm, self).__init__(*args, **kwargs)
        self.helper = ModelMethodsFormHelper(allow_edit, res_short_id, element_id, element_name='ModelMethods')

    class Meta:
        model = ModelMethods
        fields = ['runoff_calculation_method',
                  'flow_routing_method',
                  'PET_estimation_method']
        exclude = ['content_object']


class ModelMethodsValidationForm(forms.Form):
    runoff_calculation_method = forms.CharField(max_length=500, required=False)
    flow_routing_method = forms.CharField(max_length=500, required=False)
    PET_estimation_method = forms.CharField(max_length=500, required=False)

class SWATModelParametersFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('has_crop_rotation', css_class=field_width),
                        Field('has_title_drainage', css_class=field_width),
                        Field('has_point_source', css_class=field_width),
                        Field('has_fertilizer', css_class=field_width),
                        Field('has_tillage_operation', css_class=field_width),
                        Field('has_inlet_of_draining_watershed', css_class=field_width),
                        Field('has_irrigation_operation', css_class=field_width),
                        Field('has_other_parameters', css_class=field_width),
                 )
        kwargs['element_name_label'] = 'SWAT model used parameters'
        super(SWATModelParametersFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SWATModelParametersForm(ModelForm):
    has_crop_rotation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_title_drainage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_point_source = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_fertilizer = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_tillage_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_inlet_of_draining_watershed = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)
    has_irrigation_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect)


    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SWATModelParametersForm, self).__init__(*args, **kwargs)
        self.helper = SWATModelParametersFormHelper(allow_edit, res_short_id, element_id, element_name='SWATModelParameters')
        self.fields['has_crop_rotation'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_title_drainage'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_point_source'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_fertilizer'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_tillage_operation'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_inlet_of_draining_watershed'].widget.attrs['style'] = "width:auto;margin-top:-5px"
        self.fields['has_irrigation_operation'].widget.attrs['style'] = "width:auto;margin-top:-5px"

    class Meta:
        model = SWATModelParameters
        fields = ['has_crop_rotation',
                  'has_title_drainage',
                  'has_point_source',
                  'has_fertilizer',
                  'has_tillage_operation',
                  'has_inlet_of_draining_watershed',
                  'has_irrigation_operation',
                  'has_other_parameters']
        exclude = ['content_object']

class SWATModelParametersValidationForm(forms.Form):
    has_crop_rotation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_title_drainage = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_point_source = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_fertilizer = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_tillage_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_inlet_of_draining_watershed = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_irrigation_operation = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)
    has_other_parameters = forms.CharField(max_length=500, required=False)
