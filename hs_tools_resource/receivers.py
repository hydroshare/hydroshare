from django.dispatch import receiver

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update

from hs_tools_resource.models import ToolResource
from hs_tools_resource.forms import SupportedResTypesValidationForm, UrlBaseForm, VersionForm, \
                                    ToolIconForm, UrlBaseValidationForm


@receiver(pre_metadata_element_create, sender=ToolResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name'].lower()
    return validate_form(request, element_name)


@receiver(pre_metadata_element_update, sender=ToolResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    request = kwargs['request']
    element_name = kwargs['element_name'].lower()
    return validate_form(request, element_name)
    
    
def validate_form(request, element_name):
    if element_name == 'requesturlbase':
        element_form = UrlBaseValidationForm(data=request.POST)
    elif element_name == 'toolversion':
        element_form = VersionForm(data=request.POST)
    elif element_name == 'supportedrestypes':
        element_form = SupportedResTypesValidationForm(data=request.POST)
    elif element_name == 'toolicon':
        element_form = ToolIconForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}