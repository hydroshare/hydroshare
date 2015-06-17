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
        kwargs['element_name_label'] = 'Model objective'
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
                # for some reason the following line raises TypeError exception if there are no swat_model_objectives
                # associated with the instance of ModelObjective - thus using try ... except
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


class simulationTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('simulation_type_name'),
                 )
        kwargs['element_name_label'] = 'Simulation type'
        super(simulationTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class simulationTypeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        type_choices = (('Choose a type', 'Choose a type'),
                                   ('Normal Simulation', 'Normal Simulation'),
                                   ('Sensitivity Analysis', 'Sensitivity Analysis'),
                                   ('Auto-Calibration', 'Auto-Calibration'),)
        super(simulationTypeForm, self).__init__(*args, **kwargs)
        self.helper = simulationTypeFormHelper(allow_edit, res_short_id, element_id, element_name='simulationType')
        self.fields['simulation_type_name'].choices = type_choices

    class Meta:
        model = simulationType
        fields = ('simulation_type_name',)


class simulationTypeValidationForm(forms.Form):
    simulation_type_name = forms.CharField(max_length=100, required=False)


class ModelMethodsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('runoff_calculation_method'),
                        MetadataField('flow_routing_method'),
                        MetadataField('PET_estimation_method'),
                 )
        kwargs['element_name_label'] = 'Model Methods'
        super(ModelMethodsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelMethodsForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelMethodsForm, self).__init__(*args, **kwargs)
        self.helper = ModelMethodsFormHelper(allow_edit, res_short_id, element_id, element_name='ModelMethods')

    class Meta:
        model = ModelMethods
        fields = ('runoff_calculation_method',
                  'flow_routing_method',
                  'PET_estimation_method',)


class ModelMethodsValidationForm(forms.Form):
    runoff_calculation_method = forms.CharField(max_length=200, required=False)
    flow_routing_method = forms.CharField(max_length=200, required=False)
    PET_estimation_method = forms.CharField(max_length=200, required=False)

class SWATModelParametersFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('model_parameters'),
                        MetadataField('other_parameters'),
                 )
        kwargs['element_name_label'] = 'SWAT model used parameters'
        super(SWATModelParametersFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SWATModelParametersForm(ModelForm):
    parameters_choices = (('Crop rotation', 'Crop rotation'), ('Tile drainage', 'Tile drainage'),
                         ('Point source', 'Point source'), ('Fertilizer', 'Fertilizer'),
                         ('Tillage operation', 'Tillage operation'),
                         ('Inlet of draining watershed', 'Inlet of draining watershed'),
                         ('Irrigation operation', 'Irrigation operation'),)
    model_parameters = forms.MultipleChoiceField(choices=parameters_choices, widget=forms.CheckboxSelectMultiple(attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SWATModelParametersForm, self).__init__(*args, **kwargs)
        self.helper = SWATModelParametersFormHelper(allow_edit, res_short_id, element_id, element_name='SWATModelParameters')

    class Meta:
        model = SWATModelParameters
        fields = ('model_parameters',
                  'other_parameters',)

class SWATModelParametersValidationForm(forms.Form):
    parameters_choices = (('Crop rotation', 'Crop rotation'), ('Tile drainage', 'Tile drainage'),
                         ('Point source', 'Point source'), ('Fertilizer', 'Fertilizer'),
                         ('Tillage operation', 'Tillage operation'),
                         ('Inlet of draining watershed', 'Inlet of draining watershed'),
                         ('Irrigation operation', 'Irrigation operation'),)
    model_parameters = forms.MultipleChoiceField(choices=parameters_choices,required=False)
    other_parameters = forms.CharField(max_length=200, required=False)

class ModelInputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('warm_up_period'),
                        MetadataField('rainfall_time_step'),
                        MetadataField('routing_time_step'),
                        MetadataField('simulation_time_step'),
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

    class Meta:
        model = ModelInput
        fields = ('warm_up_period',
                  'rainfall_time_step',
                  'routing_time_step',
                  'simulation_time_step',
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
    rainfall_time_step = forms.CharField(max_length=100, required=False)
    routing_time_step = forms.CharField(max_length=100, required=False)
    simulation_time_step = forms.CharField(max_length=100, required=False)
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