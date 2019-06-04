from django.http import HttpResponseRedirect
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

    user = request.user
    if user.is_authenticated():
        user_all_accessible_resource_list = get_my_resources_list(user)
    else:  # anonymous user
        user_all_accessible_resource_list = list(BaseResource.discoverable_resources.all())

    # resource is collectable if
    # 1) Shareable=True
    # 2) OR, current user is a owner of it
    user_all_collectable_resource_list = []
    for res in user_all_accessible_resource_list:
        if res.raccess.shareable or res.raccess.owners.filter(pk=user.pk).exists():
            user_all_collectable_resource_list.append(res)

    # current contained resources list
    collection_items_list = list(content_model.resources.all())

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user,
                                               resource_edit=edit_resource,
                                               extended_metadata_layout=None,
                                               request=request)
    if edit_resource:
        candidate_resources_list = []
        for res in user_all_collectable_resource_list:
            if content_model.short_id == res.short_id:
                continue  # skip current collection resource object
            elif res in content_model.resources.all():
                continue  # skip resources that are already in current collection

            candidate_resources_list.append(res)

        context['collection_candidate'] = candidate_resources_list
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
