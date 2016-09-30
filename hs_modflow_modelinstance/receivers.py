from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
import sys

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update, \
    pre_create_resource, post_metadata_element_update

from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource, GridDimensions,\
    StudyArea, StressPeriod, BoundaryCondition, GroundWaterFlow, ModelCalibration, GeneralElements
from hs_modflow_modelinstance.forms import ModelOutputValidationForm, ExecutedByValidationForm,\
    StudyAreaValidationForm, GridDimensionsValidationForm, StressPeriodValidationForm,\
    GroundWaterFlowValidationForm, BoundaryConditionValidationForm, ModelCalibrationValidationForm,\
    ModelInputValidationForm, GeneralElementsValidationForm


@receiver(pre_create_resource, sender=MODFLOWModelInstanceResource)
def modflowmodelinstance_pre_create_resource(sender, **kwargs):
    metadata = kwargs['metadata']
    modeloutput = {'modeloutput': {'includes_output': False}}
    metadata.append(modeloutput)


@receiver(pre_metadata_element_create, sender=MODFLOWModelInstanceResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    return _process_metadata_update_create(update_or_create='create', **kwargs)


@receiver(pre_metadata_element_update, sender=MODFLOWModelInstanceResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    return _process_metadata_update_create(update_or_create='update', **kwargs)

@receiver(post_metadata_element_update, sender=MODFLOWModelInstanceResource)
def check_element_exist(sender, **kwargs):
    element_exists = False
    cls = getattr(sys.modules[__name__], kwargs['element_name'])
    element_id = kwargs['element_id']
    try:
        el = cls.objects.get(pk=element_id)
        element_exists = True
    except ObjectDoesNotExist:
        pass
    return {'element_exists': element_exists}



def _process_metadata_update_create(update_or_create, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "modeloutput":
        element_form = ModelOutputValidationForm(request.POST)
    elif element_name == 'executedby':
        element_form = ExecutedByValidationForm(request.POST)
    elif element_name == 'studyarea':
        element_form = StudyAreaValidationForm(request.POST)
    elif element_name == 'griddimensions':
        element_form = GridDimensionsValidationForm(request.POST)
    elif element_name == 'stressperiod':
        element_form = StressPeriodValidationForm(request.POST)
    elif element_name == 'groundwaterflow':
        element_form = GroundWaterFlowValidationForm(request.POST)
    elif element_name == 'boundarycondition':
        element_form = BoundaryConditionValidationForm(request.POST)
    elif element_name == 'modelcalibration':
        element_form = ModelCalibrationValidationForm(request.POST)
    elif element_name == 'modelinput':
        if update_or_create == 'update':
            # since modelinput is a repeatable element and modelinput data is displayed on the
            # landing page using formset, the data coming from a single modelinput form in the
            # request for update needs to be parsed to match with modelinput field names
            form_data = {}
            for field_name in ModelInputValidationForm().fields:
                matching_key = [key for key in request.POST if '-'+field_name in key][0]
                form_data[field_name] = request.POST[matching_key]

            element_form = ModelInputValidationForm(form_data)
        else:
            element_form = ModelInputValidationForm(request.POST)
    elif element_name == 'generalelements':
        element_form = GeneralElementsValidationForm(request.POST)
    else:
        raise Exception('Element name: "{}" is not supported by this resource type'.format(
            element_name
        ))

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}
