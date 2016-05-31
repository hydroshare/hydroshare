__author__ = 'hydro'

## Note: this module has been imported in the models.py in order to receive signals
## se the end of the models.py for the import of this module

from django.dispatch import receiver
from hs_core.signals import pre_metadata_element_create, pre_metadata_element_update
from hs_core.models import BaseResource
from forms import *

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_create, sender=GenericResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name']
    request = kwargs['request']
    if element_name == "subject":   #keywords
        element_form = SubjectsForm(data=request.POST)
    elif element_name == "description":   #abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "creator":
        element_form = CreatorValidationForm(request.POST)
    elif element_name == "contributor":
        element_form = ContributorValidationForm(request.POST)
    elif element_name == 'relation':
        element_form = RelationValidationForm(request.POST)
    elif element_name == 'source':
        element_form = SourceValidationForm(request.POST)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'fundingagency':
        element_form = FundingAgencyValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

# This handler is executed only when a metadata element is added as part of editing a resource
@receiver(pre_metadata_element_update, sender=GenericResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    element_id = kwargs['element_id']
    request = kwargs['request']
    repeatable_elements = {'creator': CreatorValidationForm,
                           'contributor': ContributorValidationForm,
                           'relation': RelationValidationForm,
                           'source': SourceValidationForm
                           }

    if element_name == 'title':
        element_form = TitleValidationForm(request.POST)
    elif element_name == "description":   #abstract
        element_form = AbstractValidationForm(request.POST)
    elif element_name == "fundingagency":
        element_form = FundingAgencyValidationForm(request.POST)
    elif element_name in repeatable_elements:
        # since element_name is a repeatable element (e.g creator) and data for the element is displayed on the
        # landing page using formset, the data coming from a single element form in the request for update
        # needs to be parsed to match with element field names
        element_validation_form = repeatable_elements[element_name]
        form_data = {}
        for field_name in element_validation_form().fields:
            matching_key = [key for key in request.POST if '-'+field_name in key][0]
            form_data[field_name] = request.POST[matching_key]

        element_form = element_validation_form(form_data)
    elif element_name == 'rights':
        element_form = RightsValidationForm(request.POST)
    elif element_name == 'language':
        element_form = LanguageValidationForm(request.POST)
    elif element_name == 'date':
        element_form = ValidDateValidationForm(request.POST)
    elif element_name == 'coverage':
        if 'type' in request.POST:
            element_form = CoverageSpatialForm(data=request.POST)
        else:
            element_form = CoverageTemporalForm(data=request.POST)

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        # TODO: need to return form errors
        return {'is_valid': False, 'element_data_dict': None}