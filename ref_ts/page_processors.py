__author__ = 'Shaun'
from mezzanine.pages.page_processors import processor_for
from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
#from forms import *
from hs_core import page_processors
from hs_core.forms import MetaDataElementDeleteForm
from django.forms.models import formset_factory
from functools import *
from hs_core.views import *

@processor_for(RefTimeSeries)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False


        context['extended_metadata_exists'] = extended_metadata_exists


    context['res_id'] = "/hsapi/_internal/%s/download-files/" % content_model.short_id
    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
