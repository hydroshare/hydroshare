from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models import Q
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.models import BaseResource
from hs_core.views import add_generic_context
from hs_core.views.utils import get_my_resources_list
from .models import CollectionResource


@processor_for(CollectionResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    # current contained resources list
    collection_items_list = list(content_model.resources.all())

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user,
                                               resource_edit=edit_resource,
                                               extended_metadata_layout=None,
                                               request=request)
    if edit_resource:
        user = request.user
        if not user.is_authenticated():
            return HttpResponseForbidden();
        user_all_accessible_resource_list = get_my_resources_list(user)

        # resource is collectable if
        # 1) Shareable=True
        # 2) OR, current user is a owner of it
        # 3) exclude this resource as well as resources already in the collection
        user_all_accessible_resource_list.exclude(short_id=content_model.short_id)\
            .exclude(id__in=content_model.resources.all())\
            .exclude(Q(raccess__shareable=False) | Q(raccess__owners__contains=user.pk))

        context['collection_candidate'] = user_all_accessible_resource_list.all()
        context['collection_res_id'] = content_model.short_id
    elif isinstance(context, HttpResponseRedirect):
        # resource view mode
        # sending user to login page
        return context

    context['deleted_resources'] = content_model.deleted_resources.all()
    context['collection'] = collection_items_list
    context['edit_mode'] = edit_resource

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
