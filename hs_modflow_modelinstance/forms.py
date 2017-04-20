from django.forms import ModelForm
from django import forms
from crispy_forms import layout
from crispy_forms.layout import Layout, HTML

from hs_core.forms import BaseFormHelper, Helper
from hs_core.hydroshare import users

from hs_modelinstance.models import ModelOutput, ExecutedBy
from hs_modflow_modelinstance.models import StudyArea, GridDimensions, StressPeriod, \
    GroundWaterFlow, BoundaryCondition, ModelCalibration, ModelInput, GeneralElements


class MetadataField(layout.Field):
    def __init__(self, *args, **kwargs):
        kwargs['css_class'] = 'form-control input-sm'
        super(MetadataField, self).__init__(*args, **kwargs)


# ModelOutput element forms
class ModelOutputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('includes_output'),
                 )
        kwargs['element_name_label'] = 'Includes output files?'
        super(ModelOutputFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                    element_name, layout,  *args, **kwargs)


class ModelOutputForm(ModelForm):
    includes_output = forms.TypedChoiceField(choices=((True, 'Yes'), (False, 'No')),
                                             widget=forms.RadioSelect(
                                                 attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelOutputForm, self).__init__(*args, **kwargs)
        self.helper = ModelOutputFormHelper(allow_edit, res_short_id, element_id,
                                            element_name='ModelOutput')

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
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):

        # pop the model program shortid out of the kwargs dictionary
        mp_id = kwargs.pop('mpshortid')

        # get all model program resources and build option HTML elements for each one.
        # ModelProgram shortid is concatenated to the selectbox id so that it is accessible in the
        # template.
        mp_resource = users.get_resource_list(type=['ModelProgramResource'])
        options = '\n'.join(['<option value=%s>%s</option>' % (r.short_id, r.title) for r in
                             mp_resource])
        options = '<option value=Unspecified>Unspecified</option>' + options
        selectbox = HTML('<div class="div-selectbox">'
                         ' <select class="selectbox" id="selectbox_'+mp_id+'">' + options +
                         '</select>'
                         '</div><br>')

        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
            MetadataField('model_name', style="display:none"),
            selectbox,
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
        super(ExecutedByFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                   element_name, layout, *args, **kwargs)


class ExecutedByForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ExecutedByForm, self).__init__(*args, **kwargs)

        # set mpshort id to 'Unspecified' if a foreign key has not been established yet,
        # otherwise use mp short id
        mpshortid = 'Unspecified'
        if self.instance.model_program_fk is not None:
            mpshortid = self.instance.model_program_fk.short_id
        kwargs = dict(mpshortid=mpshortid)
        self.helper = ExecutedByFormHelper(allow_edit, res_short_id, element_id,
                                           element_name='ExecutedBy', **kwargs)

    class Meta:
        model = ExecutedBy
        exclude = ('content_object', 'model_program_fk',)


class ExecutedByValidationForm(forms.Form):
    model_name = forms.CharField(max_length=200)


# StudyArea element forms
class StudyAreaFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('totalLength'),
                        MetadataField('totalWidth'),
                        MetadataField('maximumElevation'),
                        MetadataField('minimumElevation'),
        )
        kwargs['element_name_label'] = 'Study Area'
        super(StudyAreaFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                  element_name, layout,  *args, **kwargs)


class StudyAreaForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(StudyAreaForm, self).__init__(*args, **kwargs)
        self.helper = StudyAreaFormHelper(allow_edit, res_short_id, element_id,
                                          element_name='StudyArea')

    class Meta:
        model = StudyArea
        fields = ('totalLength',
                  'totalWidth',
                  'maximumElevation',
                  'minimumElevation',
                  )


class StudyAreaValidationForm(forms.Form):
    totalLength = forms.CharField(max_length=100, required=False)
    totalWidth = forms.CharField(max_length=100, required=False)
    maximumElevation = forms.CharField(max_length=100, required=False)
    minimumElevation = forms.CharField(max_length=100, required=False)


# GridDimensions element forms
class GridDimensionsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('numberOfLayers'),
                        MetadataField('typeOfRows'),
                        MetadataField('numberOfRows'),
                        MetadataField('typeOfColumns'),
                        MetadataField('numberOfColumns'),
        )
        kwargs['element_name_label'] = 'Grid Dimensions'
        super(GridDimensionsFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                       element_name, layout, *args, **kwargs)


class GridDimensionsForm(ModelForm):
    grid_type_choices = (('Choose a type', 'Choose a type'),) + GridDimensions.gridTypeChoices

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(GridDimensionsForm, self).__init__(*args, **kwargs)
        self.helper = GridDimensionsFormHelper(allow_edit, res_short_id, element_id,
                                               element_name='GridDimensions')
        self.fields['typeOfRows'].choices = self.grid_type_choices
        self.fields['typeOfColumns'].choices = self.grid_type_choices

    class Meta:
        model = GridDimensions
        fields = ('numberOfLayers',
                  'typeOfRows',
                  'numberOfRows',
                  'typeOfColumns',
                  'numberOfColumns',
                  )


class GridDimensionsValidationForm(forms.Form):
    numberOfLayers = forms.CharField(max_length=100, required=False)
    typeOfRows = forms.CharField(max_length=100, required=False)
    numberOfRows = forms.CharField(max_length=100, required=False)
    typeOfColumns = forms.CharField(max_length=100, required=False)
    numberOfColumns = forms.CharField(max_length=100, required=False)


# StressPeriod element forms
class StressPeriodFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('stressPeriodType'),
                        MetadataField('steadyStateValue'),
                        MetadataField('transientStateValueType'),
                        MetadataField('transientStateValue'),
        )
        kwargs['element_name_label'] = 'Stress Period'
        super(StressPeriodFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                     element_name, layout, *args, **kwargs)


class StressPeriodForm(ModelForm):
    stress_period_type_choices = \
        (('Choose a type', 'Choose a type'),) + StressPeriod.stressPeriodTypeChoices
    transient_state_value_type_choices = \
        (('Choose a type', 'Choose a type'),) + StressPeriod.transientStateValueTypeChoices

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(StressPeriodForm, self).__init__(*args, **kwargs)
        self.helper = StressPeriodFormHelper(allow_edit, res_short_id, element_id,
                                             element_name='StressPeriod')
        self.fields['stressPeriodType'].choices = self.stress_period_type_choices
        self.fields['transientStateValueType'].choices = self.transient_state_value_type_choices

    class Meta:
        model = StressPeriod
        fields = ('stressPeriodType',
                  'steadyStateValue',
                  'transientStateValueType',
                  'transientStateValue',
                  )


class StressPeriodValidationForm(forms.Form):
    stressPeriodType = forms.CharField(max_length=100, required=False)
    steadyStateValue = forms.CharField(max_length=100, required=False)
    transientStateValueType = forms.CharField(max_length=100, required=False)
    transientStateValue = forms.CharField(max_length=100, required=False)


# GroundWaterFlow element forms
class GroundWaterFlowFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('flowPackage'),
                        MetadataField('flowParameter'),
        )
        kwargs['element_name_label'] = 'Groundwater Flow'
        super(GroundWaterFlowFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout, *args, **kwargs)


class GroundWaterFlowForm(ModelForm):
    flow_package_choices = \
        (('Choose a package', 'Choose a package'),) + GroundWaterFlow.flowPackageChoices
    flow_parameter_choices = \
        (('Choose a parameter', 'Choose a parameter'),) + GroundWaterFlow.flowParameterChoices

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(GroundWaterFlowForm, self).__init__(*args, **kwargs)
        self.helper = GroundWaterFlowFormHelper(allow_edit, res_short_id, element_id,
                                                element_name='GroundWaterFlow')
        self.fields['flowPackage'].choices = self.flow_package_choices
        self.fields['flowParameter'].choices = self.flow_parameter_choices

    class Meta:
        model = GroundWaterFlow
        fields = ('flowPackage',
                  'flowParameter',
                  )


class GroundWaterFlowValidationForm(forms.Form):
    flowPackage = forms.CharField(max_length=100, required=False)
    flowParameter = forms.CharField(max_length=100, required=False)


# BoundaryCondition element forms
class BoundaryConditionFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('specified_head_boundary_packages'),
                        MetadataField('other_specified_head_boundary_packages'),
                        MetadataField('specified_flux_boundary_packages'),
                        MetadataField('other_specified_flux_boundary_packages'),
                        MetadataField('head_dependent_flux_boundary_packages'),
                        MetadataField('other_head_dependent_flux_boundary_packages'),
                 )
        kwargs['element_name_label'] = 'Boundary Condition'
        super(BoundaryConditionFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                          element_name, layout, *args, **kwargs)


class BoundaryConditionForm(ModelForm):
    specified_head_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.specifiedHeadBoundaryPackageChoices,
        widget=forms.CheckboxSelectMultiple(attrs={'style': 'width:auto;margin-top:-5px'}))
    specified_flux_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.specifiedFluxBoundaryPackageChoices,
        widget=forms.CheckboxSelectMultiple(attrs={'style': 'width:auto;margin-top:-5px'}))
    head_dependent_flux_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.headDependentFluxBoundaryPackageChoices,
        widget=forms.CheckboxSelectMultiple(attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(BoundaryConditionForm, self).__init__(*args, **kwargs)
        self.helper = BoundaryConditionFormHelper(allow_edit, res_short_id, element_id,
                                                  element_name='BoundaryCondition')
        if self.instance:
            if self.instance.id:
                self.fields['specified_head_boundary_packages'].initial = \
                    [types.description for types in
                     self.instance.specified_head_boundary_packages.all()]
                self.fields['specified_flux_boundary_packages'].initial = \
                    [packages.description for packages in
                     self.instance.specified_flux_boundary_packages.all()]
                self.fields['head_dependent_flux_boundary_packages'].initial = \
                    [packages.description for packages in
                     self.instance.head_dependent_flux_boundary_packages.all()]

    class Meta:
        model = BoundaryCondition
        exclude = ('specified_head_boundary_packages',
                   'specified_flux_boundary_packages',
                   'head_dependent_flux_boundary_packages',
                   )
        fields = ('other_specified_head_boundary_packages',
                  'other_specified_flux_boundary_packages',
                  'other_head_dependent_flux_boundary_packages',
                  )


class BoundaryConditionValidationForm(forms.Form):
    specified_head_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.specifiedHeadBoundaryPackageChoices, required=False)
    specified_flux_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.specifiedFluxBoundaryPackageChoices, required=False)
    head_dependent_flux_boundary_packages = forms.MultipleChoiceField(
        choices=BoundaryCondition.headDependentFluxBoundaryPackageChoices, required=False)
    other_specified_head_boundary_packages = forms.CharField(max_length=200, required=False)
    other_specified_flux_boundary_packages = forms.CharField(max_length=200, required=False)
    other_head_dependent_flux_boundary_packages = forms.CharField(max_length=200, required=False)


# ModelCalibration element forms
class ModelCalibrationFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('calibratedParameter'),
                        MetadataField('observationType'),
                        MetadataField('observationProcessPackage'),
                        MetadataField('calibrationMethod'),
        )
        kwargs['element_name_label'] = 'Model Calibration'
        super(ModelCalibrationFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout, *args, **kwargs)


class ModelCalibrationForm(ModelForm):
    observation_process_package_choices = (('Choose a package', 'Choose a package'),) + \
                                          ModelCalibration.observationProcessPackageChoices

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelCalibrationForm, self).__init__(*args, **kwargs)
        self.helper = ModelCalibrationFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='ModelCalibration')
        self.fields['observationProcessPackage'].choices = self.observation_process_package_choices

    class Meta:
        model = ModelCalibration
        fields = ('calibratedParameter',
                  'observationType',
                  'observationProcessPackage',
                  'calibrationMethod',
                  )


class ModelCalibrationValidationForm(forms.Form):
    calibratedParameter = forms.CharField(max_length=100, required=False)
    observationType = forms.CharField(max_length=100, required=False)
    observationProcessPackage = forms.CharField(max_length=100, required=False)
    calibrationMethod = forms.CharField(max_length=100, required=False)


# ModelInput element forms
class ModelInputFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('inputType'),
                        MetadataField('inputSourceName'),
                        MetadataField('inputSourceURL'),
        )
        kwargs['element_name_label'] = 'Model Input'
        super(ModelInputFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                   element_name, layout, *args, **kwargs)


class ModelInputForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ModelInputForm, self).__init__(*args, **kwargs)
        self.helper = ModelInputFormHelper(allow_edit, res_short_id, element_id,
                                           element_name='ModelInput')

        if res_short_id:
            self.action = "/hsapi/_internal/%s/modelinput/add-metadata/" % res_short_id
        else:
            self.action = ""

    @property
    def form_id(self):
        form_id = 'id_modelinput_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = ModelInput
        fields = ('inputType',
                  'inputSourceName',
                  'inputSourceURL',
                  )


class ModelInputValidationForm(forms.Form):
    inputType = forms.CharField(max_length=100, required=False)
    inputSourceName = forms.CharField(max_length=100, required=False)
    inputSourceURL = forms.URLField(required=False)


# GeneralElements element forms
class GeneralElementsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields
        # will be displayed
        layout = Layout(
                        MetadataField('modelParameter'),
                        MetadataField('modelSolver'),
                        MetadataField('output_control_package'),
                        MetadataField('subsidencePackage'),
        )
        kwargs['element_name_label'] = 'General'
        super(GeneralElementsFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout, *args, **kwargs)


class GeneralElementsForm(ModelForm):
    model_solver_choices = \
        (('Choose a solver', 'Choose a solver'),) + GeneralElements.modelSolverChoices
    output_control_package = forms.MultipleChoiceField(
        choices=GeneralElements.outputControlPackageChoices,
        widget=forms.CheckboxSelectMultiple(attrs={'style': 'width:auto;margin-top:-5px'}))
    subsidence_package_choices = \
        (('Choose a package', 'Choose a package'),) + GeneralElements.subsidencePackageChoices

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(GeneralElementsForm, self).__init__(*args, **kwargs)
        self.helper = GeneralElementsFormHelper(allow_edit, res_short_id, element_id,
                                                element_name='GeneralElements')
        self.fields['modelSolver'].choices = self.model_solver_choices
        self.fields['subsidencePackage'].choices = self.subsidence_package_choices
        if self.instance:
            if self.instance.id:
                self.fields['output_control_package'].initial = \
                    [types.description for types in self.instance.output_control_package.all()]

    class Meta:
        model = GeneralElements
        exclude = ('output_control_package',)
        fields = ('modelParameter',
                  'modelSolver',
                  'subsidencePackage',
                  )


class GeneralElementsValidationForm(forms.Form):
    modelParameter = forms.CharField(max_length=100, required=False)
    modelSolver = forms.CharField(max_length=100, required=False)
    output_control_package = forms.MultipleChoiceField(
        choices=GeneralElements.outputControlPackageChoices,
        required=False)
    subsidencePackage = forms.CharField(max_length=100, required=False)


ModelInputLayoutEdit = Layout(
        HTML('<div class="col-xs-12 col-sm-6"> '
             '<div class="form-group" id="modelinput"> '
             '{% load crispy_forms_tags %} '
             '{% for form in model_input_formset.forms %} '
             '<form id="{{form.form_id}}" action="{{ form.action }}" '
             'method="POST" enctype="multipart/form-data"> '
             '{% crispy form %} '
             '<div class="row" style="margin-top:10px">'
             '<div class="col-md-12">'
             '<span class="glyphicon glyphicon-trash icon-button btn-remove" data-toggle="modal" '
             'data-placement="auto" title="Delete Model Input" '
             'data-target="#delete-modelinput-element-dialog_{{ form.number }}"></span>'
             '</div>'
             '<div class="col-md-3">'
             '<button type="button" class="btn btn-primary pull-right btn-form-submit">'
             'Save changes</button>'  # TODO: TESTING
             '</div>'
             '</div>'
             '{% crispy form.delete_modal_form %} '
             '</form> '
             '{% endfor %}</div>'
             '</div> '
             ),
        HTML('<div style="margin-top:10px" class="col-md-2">'
             '<p><a id="add-modelinput" class="btn btn-success" data-toggle="modal" '
             'data-target="#add-modelinput-dialog">'
             '<i class="fa fa-plus"></i>Add Model Input</a>'
             '</div>'
             ),
)


ModalDialogLayoutAddModelInput = Helper.get_element_add_modal_form('ModelInput',
                                                                   'add_modelinput_modal_form')
