__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms
from crispy_forms import *
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper


model_objective_choices = (
                            ('Hydrology', 'Hydrology'),
                            ('Water quality', 'Water quality'),
                            ('BMPs', 'BMPs'),
                            ('Climate / Landuse Change', 'Climate / Landuse Change'),
                          )

parameters_choices = (
                        ('Crop rotation', 'Crop rotation'),
                        ('Tile drainage', 'Tile drainage'),
                        ('Point source', 'Point source'),
                        ('Fertilizer', 'Fertilizer'),
                        ('Tillage operation', 'Tillage operation'),
                        ('Inlet of draining watershed', 'Inlet of draining watershed'),
                        ('Irrigation operation', 'Irrigation operation'),
                      )

type_choices = (
                    ('Choose a type', 'Choose a type'),
                    ('Normal Simulation', 'Normal Simulation'),
                    ('Sensitivity Analysis', 'Sensitivity Analysis'),
                    ('Auto-Calibration', 'Auto-Calibration'),
                )

rainfall_type_choices = (('Choose a type', 'Choose a type'), ('Daily', 'Daily'), ('Sub-hourly', 'Sub-hourly'),)

routing_type_choices = (('Choose a type', 'Choose a type'), ('Daily', 'Daily'), ('Hourly', 'Hourly'),)

simulation_type_choices = (('Choose a type', 'Choose a type'), ('Annual', 'Annual'), ('Monthly', 'Monthly'), ('Daily', 'Daily'), ('Hourly', 'Hourly'),)

class MetadataField(layout.Field):
          def __init__(self, *args, **kwargs):
              kwargs['css_class'] = 'form-control input-sm'
              super(MetadataField, self).__init__(*args, **kwargs)

class ModelOutputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('includes_output'),
                 )
        kwargs['element_name_label'] = 'Includes output files?'
        super(ModelOutputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ModelOutputForm(ModelForm):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), widget=forms.RadioSelect(attrs={'style': 'width:auto;margin-top:-5px'}))
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelOutputForm, self).__init__(*args, **kwargs)
        self.helper = ModelOutputFormHelper(allow_edit, res_short_id, element_id, element_name='ModelOutput')

    class Meta:
        model = ModelOutput
        fields = ('includes_output',)

class ModelOutputValidationForm(forms.Form):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')), required=False)

    def clean_includes_output(self):
        data = self.cleaned_data['includes_output']
        if data == u'False':
            return False
        else:
            return True

class ExecutedByFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('name'),
                 )

        kwargs['element_name_label'] = 'Model Program used for execution'
        super(ExecutedByFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ExecutedByForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ExecutedByForm, self).__init__(*args, **kwargs)
        self.helper = ExecutedByFormHelper(allow_edit, res_short_id, element_id, element_name='ExecutedBy')

    class Meta:
        model = ExecutedBy
        fields = ('name',)

class ExecutedByValidationForm(forms.Form):
    name = forms.CharField(max_length=200)


class ModelObjectiveFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('swat_model_objectives'),
                        MetadataField('other_objectives'),
                 )
        kwargs['element_name_label'] = 'Model Objective'
        super(ModelObjectiveFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelObjectiveForm(ModelForm):
    swat_model_objectives = forms.MultipleChoiceField(choices=model_objective_choices,
                                                      widget=forms.CheckboxSelectMultiple(
                                                          attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelObjectiveForm, self).__init__(*args, **kwargs)
        self.helper = ModelObjectiveFormHelper(allow_edit, res_short_id, element_id, element_name='ModelObjective')
        if self.instance:
            try:
                swat_model_objectives = self.instance.swat_model_objectives.all()
                if len(swat_model_objectives) > 0:
                    self.fields['swat_model_objectives'].initial = [objective.description for objective in
                                                                    swat_model_objectives]
                else:
                    self.fields['swat_model_objectives'].initial = []
            except TypeError:
                self.fields['swat_model_objectives'].initial = []

    class Meta:
        model = ModelObjective
        fields = ('other_objectives',)


class ModelObjectiveValidationForm(forms.Form):
    swat_model_objectives = forms.MultipleChoiceField(choices=model_objective_choices, required=False)
    other_objectives = forms.CharField(max_length=200, required=False)


class SimulationTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('simulation_type_name'),
                 )
        kwargs['element_name_label'] = 'Simulation Type'
        super(SimulationTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SimulationTypeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SimulationTypeForm, self).__init__(*args, **kwargs)
        self.helper = SimulationTypeFormHelper(allow_edit, res_short_id, element_id, element_name='SimulationType')
        self.fields['simulation_type_name'].choices = type_choices

    class Meta:
        model = SimulationType
        fields = ('simulation_type_name',)


class SimulationTypeValidationForm(forms.Form):
    simulation_type_name = forms.CharField(max_length=100, required=False)


class ModelMethodFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('runoff_calculation_method'),
                        MetadataField('flow_routing_method'),
                        MetadataField('PET_estimation_method'),
                 )
        kwargs['element_name_label'] = 'Model Method'
        super(ModelMethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelMethodForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelMethodForm, self).__init__(*args, **kwargs)
        self.helper = ModelMethodFormHelper(allow_edit, res_short_id, element_id, element_name='ModelMethod')

    class Meta:
        model = ModelMethod
        fields = ('runoff_calculation_method',
                  'flow_routing_method',
                  'PET_estimation_method',)


class ModelMethodValidationForm(forms.Form):
    runoff_calculation_method = forms.CharField(max_length=200, required=False)
    flow_routing_method = forms.CharField(max_length=200, required=False)
    PET_estimation_method = forms.CharField(max_length=200, required=False)

class ModelParameterFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('model_parameters'),
                        MetadataField('other_parameters'),
                 )
        kwargs['element_name_label'] = 'Model Parameter'
        super(ModelParameterFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ModelParameterForm(ModelForm):
    model_parameters = forms.MultipleChoiceField(choices=parameters_choices,
                                                 widget=forms.CheckboxSelectMultiple(
                                                     attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelParameterForm, self).__init__(*args, **kwargs)
        self.helper = ModelParameterFormHelper(allow_edit, res_short_id, element_id, element_name='ModelParameter')
        if self.instance:
            try:
                model_parameters = self.instance.model_parameters.all()
                if len(model_parameters) > 0:
                    self.fields['model_parameters'].initial = [parameter.description for parameter in
                                                                    model_parameters]
                else:
                    self.fields['model_parameters'].initial = []
            except TypeError:
                self.fields['model_parameters'].initial = []
    class Meta:
        model = ModelParameter
        fields = ('other_parameters',)

class ModelParameterValidationForm(forms.Form):
    model_parameters = forms.MultipleChoiceField(choices=parameters_choices,required=False)
    other_parameters = forms.CharField(max_length=200, required=False)

class ModelInputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('warm_up_period'),
                        MetadataField('rainfall_time_step_type'),
                        MetadataField('rainfall_time_step_value'),
                        MetadataField('routing_time_step_type'),
                        MetadataField('routing_time_step_value'),
                        MetadataField('simulation_time_step_type'),
                        MetadataField('simulation_time_step_value'),
                        MetadataField('watershed_area'),
                        MetadataField('number_of_subbasins'),
                        MetadataField('number_of_HRUs'),
                        MetadataField('DEM_resolution'),
                        MetadataField('DEM_source_name'),
                        MetadataField('DEM_source_URL'),
                        MetadataField('landUse_data_source_name'),
                        MetadataField('landUse_data_source_URL'),
                        MetadataField('soil_data_source_name'),
                        MetadataField('soil_data_source_URL'),
                 )
        kwargs['element_name_label'] = 'Model Input'
        super(ModelInputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelInputForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelInputForm, self).__init__(*args, **kwargs)
        self.helper = ModelInputFormHelper(allow_edit, res_short_id, element_id, element_name='ModelInput')
        self.fields['rainfall_time_step_type'].choices = rainfall_type_choices
        self.fields['routing_time_step_type'].choices = routing_type_choices
        self.fields['simulation_time_step_type'].choices = simulation_type_choices

    class Meta:
        model = ModelInput
        fields = ('warm_up_period',
                  'rainfall_time_step_type',
                  'rainfall_time_step_value',
                  'routing_time_step_type',
                  'routing_time_step_value',
                  'simulation_time_step_type',
                  'simulation_time_step_value',
                  'watershed_area',
                  'number_of_subbasins',
                  'number_of_HRUs',
                  'DEM_resolution',
                  'DEM_source_name',
                  'DEM_source_URL',
                  'landUse_data_source_name',
                  'landUse_data_source_URL',
                  'soil_data_source_name',
                  'soil_data_source_URL',)


class ModelInputValidationForm(forms.Form):
    warm_up_period = forms.CharField(max_length=100, required=False)
    rainfall_time_step_type = forms.CharField(max_length=100, required=False)
    rainfall_time_step_value = forms.CharField(max_length=100, required=False)
    routing_time_step_type = forms.CharField(max_length=100, required=False)
    routing_time_step_value = forms.CharField(max_length=100, required=False)
    simulation_time_step_type = forms.CharField(max_length=100, required=False)
    simulation_time_step_value = forms.CharField(max_length=100, required=False)
    watershed_area = forms.CharField(max_length=100, required=False)
    number_of_subbasins = forms.CharField(max_length=100, required=False)
    number_of_HRUs = forms.CharField(max_length=100, required=False)
    DEM_resolution = forms.CharField(max_length=100, required=False)
    DEM_source_name = forms.CharField(max_length=200, required=False)
    DEM_source_URL = forms.URLField(required=False)
    landUse_data_source_name = forms.CharField(max_length=200, required=False)
    landUse_data_source_URL = forms.URLField(required=False)
    soil_data_source_name = forms.CharField(max_length=200, required=False)
    soil_data_source_URL = forms.URLField(required=False)