from django.db.models import Q
from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_core.views.utils import authorize
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
        user_all_accessible_resource_list = list(BaseResource.objects.\
                                                 filter(Q(raccess__public=True) | Q(raccess__discoverable=True)).distinct())

    collection_items_list = None
    collection_items_accessible = []
    collection_items_inaccessible = []
    if content_model.metadata.collection_items.first():
        collection_items_list = list(content_model.metadata.collection_items.first().collection_items.all())
        for res in collection_items_list:
            if res in user_all_accessible_resource_list or res.raccess.discoverable or res.raccess.public:
                collection_items_accessible.append(res)
            else:
                collection_items_inaccessible.append(res)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=None,
                                                   request=request)
        extended_metadata_exists = False

        collection_message = ""
        if collection_items_list is not None:
            collection_length = len(collection_items_list)
            collection_message = "This collection holds {0} resource(s) in total. ".format(collection_length)
            hide_count = len(collection_items_inaccessible)
            if hide_count > 0:
                collection_message += "You have NO permission to view the {} grey resource(s). \
                You could try to request for permission by leaving a comment below.".format(hide_count)

        if collection_items_list is not None:
            extended_metadata_exists = True

            link_html = ""
            for res in collection_items_accessible:
                sharing_status = get_sharing_status_string(res)
                link_html += '<a style="color: blue" href="/resource/' + res.short_id + '" target="_blank">' + \
                             res.resource_type + ' : ' + res.title + ' : ' + sharing_status + ' : ' + \
                             res.short_id + '</a><br/>'
            for res in collection_items_inaccessible:
                sharing_status = get_sharing_status_string(res)
                link_html += '<a style="color: grey" href="/resource/' + res.short_id + '" target="_blank">' + \
                             res.resource_type + ' : ' + res.title + ' : ' + sharing_status + ' : ' + \
                             res.short_id + '</a><br/>'
            context['collection_items'] = link_html

            if hide_count > 0:
                context['collection_message'] = collection_message

        context['extended_metadata_exists'] = extended_metadata_exists
    else:

        collection_itmes_meta = content_model.metadata.collection_items.first()
        candidate_resources_list = []
        for res in user_all_accessible_resource_list:
            if content_model.short_id == res.short_id:
                continue # skip current collection resource object
            elif collection_itmes_meta is not None and res in collection_itmes_meta.collection_items.all():
                continue # skip resources that are already in current collection
            elif res.resource_type.lower() == "collectionresource":
                continue # skip the res that is type of collection
            candidate_resources_list.append(res)

        disable_private_flag = False
        if authorize(request, content_model.short_id, edit=True, raises_exception=False)[1] and \
                not authorize(request, content_model.short_id, full=True, raises_exception=False)[1]:
            # if current user has Edit permission but not owner
            if content_model.raccess.public or content_model.raccess.discoverable:
                # if current sharing status is public or discoveralbe
                disable_private_flag = True

        color_code_with_permission = "blue"
        color_code_no_permission = "grey"
        html_candidate = ""
        for res in candidate_resources_list:
            sharing_status = get_sharing_status_string(res)
            if disable_private_flag and sharing_status.lower() == "private":
                html_candidate += '<option disabled style="color: {0}" value="{1}">{2} : {3} : {4} : {5} (Not Selectable)</option>'\
                    .format(color_code_with_permission, res.short_id, res.resource_type, res.title, sharing_status, res.short_id)
            else:
                html_candidate += '<option style="color: {0}" value="{1}">{2} : {3} : {4} : {5}</option>'\
                    .format(color_code_with_permission, res.short_id, res.resource_type, res.title, sharing_status, res.short_id)

        html_collection = ""
        if collection_itmes_meta is not None:
            for res_checked in collection_itmes_meta.collection_items.all():
                sharing_status = get_sharing_status_string(res_checked)
                if res_checked in user_all_accessible_resource_list or res_checked.raccess.discoverable or res_checked.raccess.public:
                    html_collection += '<option style="color: {0}" value="{1}">{2} : {3} : {4} : {5}</option>'\
                    .format(color_code_with_permission, res_checked.short_id, res_checked.resource_type, \
                    res_checked.title, sharing_status, res_checked.short_id)
                else:
                    html_collection += '<option style="color: {0}" value="{1}">{2} : {3} : {4} : {5}</option>'\
                    .format(color_code_no_permission, res_checked.short_id, res_checked.resource_type, \
                    res_checked.title, sharing_status, res_checked.short_id)

        ext_md_layout = Layout(HTML(
                                    '<h4>My Resource Pool</h4>'
                                    '<select class="form-control" multiple="multiple" id="select1">'
                                ),
                                HTML(
                                    html_candidate
                                ),
                                HTML(
                                    '</select>'
                                    '<input class="btn btn-success" type="button" id="add" value ="v Add v"/>'
                                    '&nbsp;&nbsp;&nbsp;&nbsp;'
                                    '<input class="btn btn-danger" type="button" id="remove" value ="^ Remove ^" />'
                                    '<form id="collector" name="collector" action="/hsapi/_internal/' + content_model.short_id + \
                                    '/update-collection/" method="POST">'
                                    '<h4>My Collection</h4>'
                                    '<select class="form-control" multiple="multiple" id="select2" name="collection_items">'
                                ),
                                HTML(html_collection),
                                HTML('</select>'
                                     '</form>'
                                     '<br/><input class="btn btn-primary" type="button" id="save" value="Save Changes"/>'
                                )
                               )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)

        context['html_candidate'] = html_candidate
        context['html_collection'] = html_collection

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context

def get_sharing_status_string(res):
    if res.raccess.public:
        return "Public"
    elif res.raccess.discoverable:
        return "Discoverable"
    else:
        return "Private"
