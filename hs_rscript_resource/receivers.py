from django.dispatch import receiver

from hs_core.signals import *
from hs_rscript_resource.models import RScriptResource
from hs_rscript_resource.forms import *
from urlparse import urlparse


@receiver(pre_create_resource, sender=RScriptResource)
def rs_pre_trigger(sender, **kwargs):
    metadata = kwargs['metadata']
    extended_metadata = {}
    metadata.append({'rsmetadata': extended_metadata})
    return metadata


@receiver(pre_metadata_element_create, sender=RScriptResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "rsmetadata":
        element_form = RSFormValidation(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_metadata_element_update, sender=RScriptResource)
def rs_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "rsmetadata":
        element_form = RSFormValidation(request.POST)

    if element_form.is_valid():
        cleaned_form = element_form.cleaned_data
        # make sure urls contain scheme (otherwise links on landing page will not work)
        if not bool(urlparse(cleaned_form['scriptCodeRepository']).scheme) \
                and bool(urlparse(cleaned_form['scriptCodeRepository']).path):
            cleaned_form['scriptCodeRepository'] = 'http://' + cleaned_form['scriptCodeRepository']
        return {'is_valid': True, 'element_data_dict': cleaned_form}
    else:
        return {'is_valid': False, 'element_data_dict': None}

