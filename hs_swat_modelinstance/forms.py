__author__ = 'Mohamed Morsy'
from django.forms import ModelForm
from django import forms

from crispy_forms import layout
from crispy_forms.layout import Layout, Field, HTML

from hs_core.forms import BaseFormHelper
from hs_core.hydroshare import users

from hs_modelinstance.models import ModelOutput, ExecutedBy
from hs_swat_modelinstance.models import SWATModelInstanceResource, ModelObjective,\
    SimulationType, ModelMethod, ModelParameter, ModelInput

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

# ExecutedBy element forms
class ExecutedByFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
            MetadataField('model_name'),
            HTML("""
            <div id=program_details_div style="display:none">
                <table id="program_details_table" class="modelprogram">
                <tr><td>Description: </td><td></td></tr>
                <tr><td>Release Date: </td><td></td></tr>
                <tr><td>Version: </td><td></td></tr>
                <tr><td>Language: </td><td></td></tr>
                <tr><td>Operating System: </td><td></td></tr>
                <tr><td>Url: </td><td></td></tr>
            </table>
            </div>
            """),
        )

        kwargs['element_name_label'] = 'Model Program used for execution'
        super(ExecutedByFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, *args,
                                                   **kwargs)


class ExecutedByForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ExecutedByForm, self).__init__(*args, **kwargs)
        self.helper = ExecutedByFormHelper(allow_edit, res_short_id, element_id, element_name='ExecutedBy')

        # get all model program resources
        mp_resource = users.get_resource_list(type=['ModelProgramResource'])

        # set model programs resources in choice list
        CHOICES = (('Unspecified', 'Unspecified'),) + tuple((r.short_id, r.title) for r in mp_resource)

        # Set the choice lists as the file names in the content model
        self.fields['model_name'].choices = CHOICES

    class Meta:
        model = ExecutedBy
        exclude = ('content_object', 'model_program_fk',)


class ExecutedByValidationForm(forms.Form):
    model_name = forms.CharField(max_length=200)
    model_program_fk = forms


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
                        MetadataField('runoffCalculationMethod'),
                        MetadataField('flowRoutingMethod'),
                        MetadataField('petEstimationMethod'),
                 )
        kwargs['element_name_label'] = 'Model Method'
        super(ModelMethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelMethodForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelMethodForm, self).__init__(*args, **kwargs)
        self.helper = ModelMethodFormHelper(allow_edit, res_short_id, element_id, element_name='ModelMethod')

    class Meta:
        model = ModelMethod
        fields = ('runoffCalculationMethod',
                  'flowRoutingMethod',
                  'petEstimationMethod',)


class ModelMethodValidationForm(forms.Form):
    runoffCalculationMethod = forms.CharField(max_length=200, required=False)
    flowRoutingMethod = forms.CharField(max_length=200, required=False)
    petEstimationMethod = forms.CharField(max_length=200, required=False)

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
                        MetadataField('warmupPeriodValue'),
                        MetadataField('rainfallTimeStepType'),
                        MetadataField('rainfallTimeStepValue'),
                        MetadataField('routingTimeStepType'),
                        MetadataField('routingTimeStepValue'),
                        MetadataField('simulationTimeStepType'),
                        MetadataField('simulationTimeStepValue'),
                        MetadataField('watershedArea'),
                        MetadataField('numberOfSubbasins'),
                        MetadataField('numberOfHRUs'),
                        MetadataField('demResolution'),
                        MetadataField('demSourceName'),
                        MetadataField('demSourceURL'),
                        MetadataField('landUseDataSourceName'),
                        MetadataField('landUseDataSourceURL'),
                        MetadataField('soilDataSourceName'),
                        MetadataField('soilDataSourceURL'),
                 )
        kwargs['element_name_label'] = 'Model Input'
        super(ModelInputFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class ModelInputForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelInputForm, self).__init__(*args, **kwargs)
        self.helper = ModelInputFormHelper(allow_edit, res_short_id, element_id, element_name='ModelInput')
        self.fields['rainfallTimeStepType'].choices = rainfall_type_choices
        self.fields['routingTimeStepType'].choices = routing_type_choices
        self.fields['simulationTimeStepType'].choices = simulation_type_choices

    class Meta:
        model = ModelInput
        fields = ('warmupPeriodValue',
                  'rainfallTimeStepType',
                  'rainfallTimeStepValue',
                  'routingTimeStepType',
                  'routingTimeStepValue',
                  'simulationTimeStepType',
                  'simulationTimeStepValue',
                  'watershedArea',
                  'numberOfSubbasins',
                  'numberOfHRUs',
                  'demResolution',
                  'demSourceName',
                  'demSourceURL',
                  'landUseDataSourceName',
                  'landUseDataSourceURL',
                  'soilDataSourceName',
                  'soilDataSourceURL',)


class ModelInputValidationForm(forms.Form):
    warmupPeriodValue = forms.CharField(max_length=100, required=False)
    rainfallTimeStepType = forms.CharField(max_length=100, required=False)
    rainfallTimeStepValue = forms.CharField(max_length=100, required=False)
    routingTimeStepType = forms.CharField(max_length=100, required=False)
    routingTimeStepValue = forms.CharField(max_length=100, required=False)
    simulationTimeStepType = forms.CharField(max_length=100, required=False)
    simulationTimeStepValue = forms.CharField(max_length=100, required=False)
    watershedArea = forms.CharField(max_length=100, required=False)
    numberOfSubbasins = forms.CharField(max_length=100, required=False)
    numberOfHRUs = forms.CharField(max_length=100, required=False)
    demResolution = forms.CharField(max_length=100, required=False)
    demSourceName = forms.CharField(max_length=200, required=False)
    demSourceURL = forms.URLField(required=False)
    landUseDataSourceName = forms.CharField(max_length=200, required=False)
    landUseDataSourceURL = forms.URLField(required=False)
    soilDataSourceName = forms.CharField(max_length=200, required=False)
    soilDataSourceURL = forms.URLField(required=False)