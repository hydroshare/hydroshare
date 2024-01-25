from datetime import timedelta

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils import timezone
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context

from .models import CompositeResource


@processor_for(CompositeResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                               extended_metadata_layout=None, request=request)

    if isinstance(context, HttpResponseRedirect):
        # sending user to login page
        return context

    file_type_missing_metadata = {'file_type_missing_metadata':
                                  content_model.get_missing_file_type_metadata_info()}
    context.update(file_type_missing_metadata)
    if content_model.repaired:
        cuttoff_time = timezone.now() - timedelta(days=7)
        repaired = content_model.repaired >= cuttoff_time,
    else:
        repaired = False
    update = {
        'recently_repaired': repaired,
        'notify_on_repair': settings.NOTIFY_OWNERS_AFTER_RESOURCE_REPAIR
    }
    context.update(update)
    data_services_urls = {'data_services_urls':
                          content_model.get_data_services_urls()}
    context.update(data_services_urls)
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)

    # sending user to resource landing page
    return context
