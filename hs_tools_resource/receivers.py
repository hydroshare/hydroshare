from django.dispatch import receiver
from hs_core.signals import *
from hs_tools_resource.models import *
from hs_tools_resource.forms import *
from hs_core import hydroshare
from hs_core.hydroshare.resource import ResourceFile
import os
from hs_core.hydroshare import utils


@receiver(pre_metadata_element_create, sender=ToolResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name']
    element_name = element_name.lower()
    # if element_name == "fee":
    #     element_form = FeeForm(data=request.POST)
    if element_name == 'toolresourcetype':
        element_form = ResTypeForm(data=request.POST)
    elif element_name == 'requesturlbase':
        element_form = UrlBaseForm(data=request.POST)
    elif element_name == 'toolversion':
        element_form = VersionForm(data=request.POST)
    elif element_name == 'supportedrestypes':
        element_form = SupportedResTypesValidationForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=ToolResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    element_name = element_name.lower()
    request = kwargs['request']
    # if element_name == "fee":
    #     element_form = FeeForm(data=request.POST)
    if element_name == 'toolresourcetype':
        element_form = ResTypeForm(data=request.POST)
    elif element_name == 'requesturlbase':
        element_form = UrlBaseForm(data=request.POST)
    elif element_name == 'toolversion':
        element_form = VersionForm(data=request.POST)
    elif element_name == 'supportedrestypes':
        element_form = SupportedResTypesValidationForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}