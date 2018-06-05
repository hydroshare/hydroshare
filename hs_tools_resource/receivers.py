from django.dispatch import receiver

from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update, \
                            pre_create_resource

from hs_tools_resource.models import ToolResource
from hs_tools_resource.forms import SupportedResTypesValidationForm,  VersionForm, \
                                    UrlValidationForm, \
                                    SupportedSharingStatusValidationForm, RoadmapForm, \
                                    ShowOnOpenWithListForm, SupportedAggTypesValidationForm, \
                                    SupportedFileExtensionsValidationForm, \
                                    AppAggregationLevelUrlValidationForm, \
                                    AppResourceLevelUrlValidationForm, \
                                    AppFileLevelUrlValidationForm

from default_icon import default_icon_data_url


@receiver(pre_create_resource, sender=ToolResource)
def webapp_pre_create_resource(sender, **kwargs):
    metadata = kwargs['metadata']
    all_sharing_status = {'SupportedSharingStatus': {'sharing_status':
                          ["Published", "Public", "Discoverable", "Private"]}}
    metadata.append(all_sharing_status)

    # a default app icon
    tool_icon_meta = {"ToolIcon": {"data_url": default_icon_data_url}}
    metadata.append(tool_icon_meta)


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
        element_form = AppResourceLevelUrlValidationForm(data=request.POST)
    elif element_name == 'requesturlbaseaggregation':
        element_form = AppAggregationLevelUrlValidationForm(data=request.POST)
    elif element_name == 'requesturlbasefile':
        element_form = AppFileLevelUrlValidationForm(data=request.POST)
    elif element_name == 'toolversion':
        element_form = VersionForm(data=request.POST)
    elif element_name == 'supportedrestypes':
        element_form = SupportedResTypesValidationForm(data=request.POST)
    elif element_name == 'supportedaggtypes':
        element_form = SupportedAggTypesValidationForm(data=request.POST)
    elif element_name == 'toolicon':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'supportedsharingstatus':
        element_form = SupportedSharingStatusValidationForm(data=request.POST)
    elif element_name == 'supportedfileextensions':
        element_form = SupportedFileExtensionsValidationForm(data=request.POST)
    elif element_name == 'apphomepageurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'testingprotocolurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'helppageurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'sourcecodeurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'helppageurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'issuespageurl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'mailinglisturl':
        element_form = UrlValidationForm(data=request.POST)
    elif element_name == 'roadmap':
        element_form = RoadmapForm(data=request.POST)
    elif element_name == 'showonopenwithlist':
        element_form = ShowOnOpenWithListForm(data=request.POST)
    else:
        return {'is_valid': False, 'element_data_dict': None}

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}
