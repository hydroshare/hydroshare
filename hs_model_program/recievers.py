from django.dispatch import receiver
from hs_core.signals import *
from hs_model_program.models import ModelProgramResource, ModelProgramMetaData, MpMetadata
from hs_model_program.forms import *
import datetime as dt

@receiver(pre_create_resource, sender=ModelProgramResource)
def mp_pre_trigger(sender, **kwargs):
    if sender is ModelProgramResource:

        files = kwargs['files']
        metadata = kwargs['metadata']

        extended_metadata = {}

        extended_metadata['software_version'] = '1.0'
        extended_metadata['software_language'] = ''
        extended_metadata['operating_sys'] = ''
        extended_metadata['date_released'] = dt.datetime.now()
        extended_metadata['program_website'] =''
        extended_metadata['software_repo'] = ''
        extended_metadata['release_notes'] = ''
        extended_metadata['user_manual'] = ''
        extended_metadata['theoretical_manual'] =''
        extended_metadata['source_code'] = ''

        metadata.append({'mpmetadata': extended_metadata})

        return metadata


@receiver(pre_metadata_element_update, sender=ModelProgramResource)
def mp_pre_update_handler(sender, **kwargs):

    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']

    if element_name == "mpmetadata":
        element_form = mp_form_validation(request.POST)


    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

