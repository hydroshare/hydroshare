
__author__ = 'hydro'

## Note: this module has been imported in the models.py in order to receive signals
## se the end of the models.py for the import of this module

from django.dispatch import receiver
from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update
from hs_app_timeseries.models import TimeSeriesResource
from forms import *

@receiver(pre_metadata_element_create, sender=TimeSeriesResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name']
    request = kwargs['request']
    if element_name == "site":
        element_form = SiteTestForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

@receiver(pre_metadata_element_update, sender=TimeSeriesResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name']
    element_id = kwargs['element_id']
    request = kwargs['request']
    if element_name == "site":
        element_form = SiteTestForm(request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}