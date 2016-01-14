from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from forms import UrlBaseForm, VersionForm, SupportedResTypesForm, parameters_choices
from models import ToolResource, RequestUrlBase


@processor_for(ToolResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

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
                for display_name_tuple in parameters_choices:
                    if type_name.lower() == display_name_tuple[0].lower():
                        new_supported_res_types_array += [display_name_tuple[1]]
                        break

            context['supported_res_types'] = ", ".join(new_supported_res_types_array)

        context['extended_metadata_exists'] = extended_metadata_exists
        context['url_base'] = content_model.metadata.url_bases.first()
        context['version'] = content_model.metadata.versions.first()
    else:
        url_base = content_model.metadata.url_bases.first()
        if not url_base:
            url_base = RequestUrlBase.create(content_object=content_model.metadata)

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
                                                         if supported_res_types_obj else None)

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
                for parameter in supported_res_types:
                    checked_res_str += str(parameter.description)
                    checked_res_str += ","

            context['checked_res'] = checked_res_str

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
