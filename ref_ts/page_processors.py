__author__ = 'Drew, Jeff & Shaun'

from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context

from models import RefTimeSeriesResource

@processor_for(RefTimeSeriesResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                               extended_metadata_layout=None, request=request)
    extended_metadata_exists = True
    context['extended_metadata_exists'] = extended_metadata_exists

    context['download_files_url'] = "/hsapi/_internal/%s/download-files/" % content_model.short_id
    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
