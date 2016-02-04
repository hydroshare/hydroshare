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
    extended_metadata_exists = False
    if content_model.metadata.sites.all().first() or \
            content_model.metadata.variables.all().first() or \
            content_model.metadata.methods.all().first() or \
            content_model.metadata.quality_levels.all().first():
        extended_metadata_exists = True

    context['extended_metadata_exists'] = extended_metadata_exists
    context['site'] = content_model.metadata.sites.all().first()
    context['variable'] = content_model.metadata.variables.all().first()
    context['method'] = content_model.metadata.methods.all().first()
    context['quality_level'] = content_model.metadata.quality_levels.all().first
    context['referenceURL'] = content_model.metadata.referenceURLs.all().first
    context['download_files_url'] = "/hsapi/_internal/%s/download-refts-bag/" % content_model.short_id
    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
