from django.dispatch import receiver

from hs_core.signals import *
from hs_script_resource.models import ScriptResource
from hs_script_resource.forms import *

from urlparse import urlparse


@receiver(pre_create_resource, sender=ScriptResource)
def script_pre_create(sender, **kwargs):
    files = kwargs['files']
    metadata = kwargs['metadata']
    extended_metadata = {}
    script_language = None

    if files:
        file_type = files[0].name.split('.')[-1]
        if file_type.lower() == "py":
            script_language = "Python"
        elif file_type.lower() == "r":
            script_language = "R"
        elif file_type.lower() == "m":
            script_language = "MATLAB"

    if script_language:
        extended_metadata = {'scriptLanguage': script_language}

    metadata.append({'scriptspecificmetadata': extended_metadata})

    return metadata


@receiver(pre_metadata_element_create, sender=ScriptResource)
def script_metadata_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "scriptspecificmetadata":
        element_form = ScriptFormValidation(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_metadata_element_update, sender=ScriptResource)
def script_metadata_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "scriptspecificmetadata":
        element_form = ScriptFormValidation(request.POST)

    if element_form.is_valid():
        cleaned_form = element_form.cleaned_data
        # make sure urls contain scheme (otherwise links on landing page will not work)
        if not bool(urlparse(cleaned_form['scriptCodeRepository']).scheme) \
                and bool(urlparse(cleaned_form['scriptCodeRepository']).path):
            cleaned_form['scriptCodeRepository'] = 'http://' + cleaned_form['scriptCodeRepository']
        return {'is_valid': True, 'element_data_dict': cleaned_form}
    else:
        return {'is_valid': False, 'element_data_dict': None}

