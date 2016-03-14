from django.db.models import Q
from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_core.models import BaseResource
from hs_access_control.models import PrivilegeCodes

from .models import CollectionResource

@processor_for(CollectionResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    user = request.user
    if user.is_authenticated():
        # get a list of resources with effective OWNER privilege
        owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
        # get a list of resources with effective CHANGE privilege
        editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
        # get a list of resources with effective VIEW privilege
        viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)

        owned_resources = list(owned_resources)
        editable_resources = list(editable_resources)
        viewable_resources = list(viewable_resources)
        discovered_resources = list(user.ulabels.my_resources)

        user_all_accessible_resource_list = (owned_resources + editable_resources + \
                                             viewable_resources + discovered_resources)
    else: # anonymous user
        user_all_accessible_resource_list = list(BaseResource.objects. \
                                                 filter(Q(raccess__public=True) | Q(raccess__discoverable=True)).distinct())

    collection_items_list = None
    collection_items_accessible = []
    collection_items_inaccessible = []
    if content_model.metadata.collection.first():
        collection_items_list = list(content_model.metadata.collection.first().resources.all())
        for res in collection_items_list:
            if res in user_all_accessible_resource_list or res.raccess.discoverable or res.raccess.public:
                collection_items_accessible.append(res)
            else:
                collection_items_inaccessible.append(res)

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user,
                                               resource_edit=edit_resource,
                                               extended_metadata_layout=None,
                                               request=request)
    if edit_resource:
        collection_itmes_meta = content_model.metadata.collection.first()
        candidate_resources_list = []
        for res in user_all_accessible_resource_list:
            if content_model.short_id == res.short_id:
                continue # skip current collection resource object
            elif collection_itmes_meta is not None and res in collection_itmes_meta.resources.all():
                continue # skip resources that are already in current collection
            elif res.resource_type.lower() == "collectionresource":
                continue # skip the res that is type of collection
            candidate_resources_list.append(res)


    context['collection'] = collection_items_list
    if edit_resource:
         context['collection_candidate'] = candidate_resources_list
         context['collection_res_id'] = content_model.short_id
    context['edit_mode'] = edit_resource

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
