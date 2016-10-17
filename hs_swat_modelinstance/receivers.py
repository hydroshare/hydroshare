from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update,\
    pre_create_resource, post_metadata_element_update

import hs_swat_modelinstance.models as swat_models
from hs_swat_modelinstance.forms import ModelOutputValidationForm, ExecutedByValidationForm,\
    ModelObjectiveValidationForm, SimulationTypeValidationForm, ModelMethodValidationForm,\
    ModelParameterValidationForm, ModelInputValidationForm


@receiver(pre_create_resource, sender=swat_models.SWATModelInstanceResource)
def swatmodelinstance_pre_create_resource(sender, **kwargs):
    metadata = kwargs['metadata']
    modeloutput = {'modeloutput': {'includes_output': False}}
    metadata.append(modeloutput)


@receiver(pre_metadata_element_create, sender=swat_models.SWATModelInstanceResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)


@receiver(pre_metadata_element_update, sender=swat_models.SWATModelInstanceResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    return _process_metadata_update_create(**kwargs)


@receiver(post_metadata_element_update, sender=swat_models.SWATModelInstanceResource)
def check_element_exist(sender, **kwargs):
    element_id = kwargs['element_id']
    element_name = kwargs['element_name']
    element_exists = False
    class_names = vars(swat_models)
    for class_name, cls in class_names.iteritems():
        if class_name.lower() == element_name.lower():
            try:
                cls.objects.get(pk=element_id)
                element_exists = True
            except ObjectDoesNotExist:
                break
    return {'element_exists': element_exists}


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
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}