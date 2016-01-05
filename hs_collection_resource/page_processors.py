from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from forms import UrlBaseForm, VersionForm, SupportedResTypesForm, get_res_id_list
from models import CollectionResource, RequestUrlBase
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
        if content_model.metadata.url_bases.first() or content_model.metadata.versions.first():
            extended_metadata_exists = True

        new_supported_res_types_array = []
        if content_model.metadata.supported_res_types.first():
            extended_metadata_exists = True
            supported_res_types_str = content_model.metadata.supported_res_types.first().get_supported_res_types_str()
            supported_res_types_array = supported_res_types_str.split(',')
            for type_name in supported_res_types_array:
                for display_name_tuple in get_res_id_list(resource_collection):
                    if type_name.lower() == display_name_tuple.lower():
                        new_supported_res_types_array += [display_name_tuple]
                        break

            context['supported_res_types'] = ", ".join(new_supported_res_types_array)

        context['extended_metadata_exists'] = extended_metadata_exists
        context['url_base'] = content_model.metadata.url_bases.first()
        context['version'] = content_model.metadata.versions.first()
    else:
        url_base = content_model.metadata.url_bases.first()
        if not url_base:
            url_base = RequestUrlBase.create(content_object=content_model.metadata,
                                             resShortID=content_model.short_id)

        url_base_form = UrlBaseForm(instance=url_base,
                                    res_short_id=content_model.short_id,
                                    element_id=url_base.id
                                    if url_base else None)

        version = content_model.metadata.versions.first()
        version_form = VersionForm(instance=version,
                                   res_short_id=content_model.short_id,
                                   element_id=version.id
                                   if version else None)

        supported_res_types_obj = content_model.metadata.supported_res_types.first()
        supported_res_types_form = SupportedResTypesForm(instance=supported_res_types_obj,
                                                         res_short_id=content_model.short_id,
                                                         element_id=supported_res_types_obj.id
                                                         if supported_res_types_obj else None,
                                                         all_res_list=resource_collection)

        ext_md_layout = Layout(
                                HTML('<div class="form-group" id="SupportedResTypes"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy supported_res_types_form %} '
                                 '</div> '),
                                HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy url_base_form %} '
                                     '</div>'),
                                HTML('<div class="form-group col-lg-6 col-xs-12" id="version"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy version_form %} '
                                     '</div> ')
                              )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)
        context['url_base_form'] = url_base_form
        context['version_form'] = version_form
        context['supported_res_types_form'] = supported_res_types_form

        if supported_res_types_obj:
            supported_res_types = supported_res_types_obj.supported_res_types.all()
            checked_res_str = ""
            if len(supported_res_types) > 0:
                for res in supported_res_types:
                    checked_res_str += str(res.short_id)
                    checked_res_str += ","

            context['checked_res'] = checked_res_str

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
