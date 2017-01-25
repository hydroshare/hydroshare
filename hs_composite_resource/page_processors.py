from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context

from .models import CompositeResource


@processor_for(CompositeResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                               extended_metadata_layout=None, request=request)

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    return context
