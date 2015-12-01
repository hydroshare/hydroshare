import datetime as dt

from django.dispatch import receiver

from hs_core.signals import *
from hs_model_program.models import ModelProgramResource
from hs_model_program.forms import *
from urlparse import urlparse

@receiver(pre_create_resource, sender=ModelProgramResource)
def mp_pre_trigger(sender, **kwargs):
    metadata = kwargs['metadata']
    extended_metadata = {}
    metadata.append({'mpmetadata': extended_metadata})
    return metadata


@receiver(pre_metadata_element_create, sender=ModelProgramResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "mpmetadata":
        element_form = mp_form_validation(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

@receiver(pre_metadata_element_update, sender=ModelProgramResource)
def mp_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']

    if element_name == "mpmetadata":
        element_form = mp_form_validation(request.POST)

    if element_form.is_valid():
        cleaned_form = element_form.cleaned_data
        # make sure urls contain scheme (otherwise links on landing page will not work)
        if (not bool(urlparse(cleaned_form['modelWebsite']).scheme) and bool(urlparse(cleaned_form['modelWebsite']).path)):
            cleaned_form['modelWebsite'] = 'http://'+cleaned_form['modelWebsite']
        if (not bool(urlparse(cleaned_form['modelCodeRepository']).scheme) and bool(urlparse(cleaned_form['modelCodeRepository']).path)):
            cleaned_form['modelCodeRepository'] = 'http://'+cleaned_form['modelCodeRepository']
        return {'is_valid': True, 'element_data_dict': cleaned_form}
    else:
        return {'is_valid': False, 'element_data_dict': None}

