__author__ = 'Mohamed Morsy'
from django.dispatch import receiver

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update,pre_create_resource

from hs_swat_modelinstance.models import SWATModelInstanceResource
from hs_swat_modelinstance.forms import ModelOutputValidationForm, ExecutedByValidationForm,\
    ModelObjectiveValidationForm, SimulationTypeValidationForm, ModelMethodValidationForm,\
    ModelParameterValidationForm, ModelInputValidationForm


@receiver(pre_create_resource, sender=SWATModelInstanceResource)
def swatmodelinstance_pre_create_resource(sender, **kwargs):
    metadata = kwargs['metadata']
    modeloutput = {'modeloutput': {'includes_output': False}}
    metadata.append(modeloutput)

@receiver(pre_metadata_element_create, sender=SWATModelInstanceResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)

@receiver(pre_metadata_element_update, sender=SWATModelInstanceResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)

def _process_metadata_update_create(**kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "modeloutput":
        element_form = ModelOutputValidationForm(request.POST)
    elif element_name == 'executedby':
        element_form = ExecutedByValidationForm(request.POST)
    elif element_name == 'modelobjective':
        element_form = ModelObjectiveValidationForm(request.POST)
    elif element_name == 'simulationtype':
        element_form = SimulationTypeValidationForm(request.POST)
    elif element_name == 'modelmethod':
        element_form = ModelMethodValidationForm(request.POST)
    elif element_name == 'modelparameter':
        element_form = ModelParameterValidationForm(request.POST)
    elif element_name == 'modelinput':
        element_form = ModelInputValidationForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}