from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from forms import CollectionItemsForm, get_res_id_list
from models import CollectionResource
from hs_access_control.models import PrivilegeCodes, HSAccessException

@processor_for(CollectionResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    user = request.user
    # get a list of resources with effective OWNER privilege
    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    # get a list of resources with effective CHANGE privilege
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE)
    # get a list of resources with effective VIEW privilege
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW)

    owned_resources = list(owned_resources)
    editable_resources = list(editable_resources)
    viewable_resources = list(viewable_resources)
    favorite_resources = list(user.ulabels.favorited_resources)
    labeled_resources = list(user.ulabels.labeled_resources)
    discovered_resources = list(user.ulabels.my_resources)

    for res in owned_resources:
        res.owned = True

    for res in editable_resources:
        res.editable = True

    for res in viewable_resources:
        res.viewable = True

    for res in (owned_resources + editable_resources + viewable_resources + discovered_resources):
        res.is_favorite = False
        if res in favorite_resources:
            res.is_favorite = True
        if res in labeled_resources:
            res.labels = res.rlabels.get_labels(user)

    resource_collection = (owned_resources + editable_resources + viewable_resources + discovered_resources)


    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=None,
                                                   request=request)
        extended_metadata_exists = False
        if content_model.metadata.collection_items.first():
            extended_metadata_exists = True

        if content_model.metadata.collection_items.first():
            extended_metadata_exists = True

            get_info = content_model.metadata.collection_items.first().collection_items.all()
            link_html = ""
            for res in get_info:
                link_html += '<a href="/resource/'+res.short_id+'">'+ res.title +':'+ res.resource_type + '</a><br/>'
            context['collection_items'] = link_html

        context['extended_metadata_exists'] = extended_metadata_exists
    else:

        actual_resources = []
        for res in resource_collection:
            if content_model.short_id == res.short_id:
                continue
            actual_resources.append(res)

        collection_items_obj = content_model.metadata.collection_items.first()
        collection_items_form = CollectionItemsForm(instance=collection_items_obj,
                                                         res_short_id=content_model.short_id,
                                                         element_id=collection_items_obj.id
                                                         if collection_items_obj else None,
                                                         all_res_list=actual_resources)

        ext_md_layout = Layout(
                                HTML('<div class="form-group" id="CollectionItems"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy collection_items_form %} '
                                 '</div> ')
                              )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)

        context['collection_items_form'] = collection_items_form

        if collection_items_obj:
            collection_items = collection_items_obj.collection_items.all()
            checked_res_str = ""
            if len(collection_items) > 0:
                for res in collection_items:
                    checked_res_str += str(res.short_id)
                    checked_res_str += ","

            context['checked_res'] = checked_res_str

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
