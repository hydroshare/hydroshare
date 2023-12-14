from django.http import HttpResponseForbidden, HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.views import add_generic_context
from .models import CollectionResource


@processor_for(CollectionResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    # current contained resources list
    collection_items_list = list(content_model.resources.all().select_related('raccess'))

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user,
                                               resource_edit=edit_resource,
                                               extended_metadata_layout=None,
                                               request=request)
    if edit_resource:
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden()

        context['collection_res_id'] = content_model.short_id
    elif isinstance(context, HttpResponseRedirect):
        # resource view mode
        # sending user to login page
        return context

    context['deleted_resources'] = content_model.deleted_resources
    context['collection'] = collection_items_list
    context['edit_mode'] = edit_resource

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
