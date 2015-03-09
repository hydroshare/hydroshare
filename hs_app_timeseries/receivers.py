
__author__ = 'pabitra'

## Note: this module has been imported in the models.py in order to receive signals
## se the end of the models.py for the import of this module

from django.dispatch import receiver
from hs_core.signals import *
from hs_app_timeseries.models import TimeSeriesResource
from forms import *
import os

# check if the uploaded files are valid"
@receiver(pre_create_resource, sender=TimeSeriesResource)
def resource_pre_create_handler(sender, **kwargs):
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']

    # check if more than one file uploaded - only one file is allowed
    if len(files) > 1:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Only one file can be uploaded.'
    elif len(files) == 1:
        # check file extension matches with the supported file types
        uploaded_file = files[0]
        file_ext = os.path.splitext(uploaded_file.name)[1]
        if file_ext not in TimeSeriesResource.get_supported_upload_file_types():
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Invalid file type.'

# check the file to be added is valid
@receiver(pre_add_files_to_resource, sender=TimeSeriesResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    # TODO: implement
    pass

@receiver(pre_metadata_element_create, sender=TimeSeriesResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

    if element_name == "site":
        element_form = SiteValidationForm(request.POST)
    elif element_name == 'variable':
        element_form = VariableValidationForm(request.POST)
    elif element_name == 'method':
        element_form = MethodValidationForm(request.POST)
    elif element_name == 'processinglevel':
        element_form = ProcessingLevelValidationForm(request.POST)
    elif element_name == 'timeseriesresult':
        element_form = TimeSeriesResultValidationForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

@receiver(pre_metadata_element_update, sender=TimeSeriesResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']

    if element_name == "site":
        element_form = SiteValidationForm(request.POST)
    elif element_name == 'variable':
        element_form = VariableValidationForm(request.POST)
    elif element_name == 'method':
        element_form = MethodValidationForm(request.POST)
    elif element_name == 'processinglevel':
        element_form = ProcessingLevelValidationForm(request.POST)
    elif element_name == 'timeseriesresult':
        element_form = TimeSeriesResultValidationForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

"""
 Since each of the timeseries metadata element is required no need to listen to any delete signal
 The timeseries landing page should not have delete UI functionality for the resource specific metadata elements
"""