from mezzanine.pages.page_processors import processor_for
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from forms import UrlBaseForm, VersionForm, SupportedResTypesForm, ToolIconForm, \
                  SupportedSharingStatusForm, AppHomePageUrlForm, SupportedFileTypesForm
from models import ToolResource
from utils import get_SupportedResTypes_choices, get_SupportedFileTypes_choices


@processor_for(ToolResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if content_model.metadata.supported_sharing_statuses is None:
        content_model.metadata.create_element('SupportedSharingStatus',
                                              sharing_status=['Published', 'Public',
                                                              'Discoverable', 'Private'],)
    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=None,
                                                   request=request)
        extended_metadata_exists = False
        if content_model.metadata.url_base or content_model.metadata.version:
            extended_metadata_exists = True

        new_supported_res_types_array = []
        if content_model.metadata.supported_res_types:
            extended_metadata_exists = True
            supported_res_types_str = content_model.metadata.\
                supported_res_types.get_supported_res_types_str()
            supported_res_types_array = supported_res_types_str.split(',')
            for type_name in supported_res_types_array:
                for class_verbose_list in get_SupportedResTypes_choices():
                    if type_name.lower() == class_verbose_list[0].lower():
                        new_supported_res_types_array += [class_verbose_list[1]]
                        break

            context['supported_res_types'] = ", ".join(new_supported_res_types_array)

        new_supported_file_types_array = []
        if content_model.metadata.supported_file_types:
            extended_metadata_exists = True
            supported_file_types_str = content_model.metadata.\
                supported_file_types.get_supported_file_types_str()
            supported_file_types_array = supported_file_types_str.split(',')
            for type_name in supported_file_types_array:
                for class_verbose_list in get_SupportedFileTypes_choices():
                    if type_name.lower() == class_verbose_list[0].lower():
                        new_supported_file_types_array += [class_verbose_list[1]]
                        break

            context['supported_file_types'] = ", ".join(new_supported_file_types_array)

        if content_model.metadata.supported_sharing_statuses is not None:
            extended_metadata_exists = True
            sharing_status_str = content_model.metadata.supported_sharing_statuses\
                .get_sharing_status_str()
            context['supported_sharing_status'] = sharing_status_str


        if content_model.metadata.app_icon:
            context['tool_icon_url'] = content_model.metadata.app_icon.data_url

        context['extended_metadata_exists'] = extended_metadata_exists
        context['url_base'] = content_model.metadata.url_base
        context['version'] = content_model.metadata.version
        context['homepage_url'] = content_model.metadata.app_home_page_url

    else:
        url_base = content_model.metadata.url_base
        url_base_form = UrlBaseForm(instance=url_base,
                                    res_short_id=content_model.short_id,
                                    element_id=url_base.id
                                    if url_base else None)

        homepage_url = content_model.metadata.app_home_page_url
        homepage_url_form = \
            AppHomePageUrlForm(instance=homepage_url,
                               res_short_id=content_model.short_id,
                               element_id=homepage_url.id
                               if homepage_url else None)

        version = content_model.metadata.version
        version_form = VersionForm(instance=version,
                                   res_short_id=content_model.short_id,
                                   element_id=version.id
                                   if version else None)

        supported_res_types_obj = content_model.metadata.supported_res_types
        supported_res_types_form = SupportedResTypesForm(instance=supported_res_types_obj,
                                                         res_short_id=content_model.short_id,
                                                         element_id=supported_res_types_obj.id
                                                         if supported_res_types_obj else None)

        supported_file_types_obj = content_model.metadata.supported_file_types
        supported_file_types_form = SupportedFileTypesForm(instance=supported_file_types_obj,
                                                           res_short_id=content_model.short_id,
                                                           element_id=supported_file_types_obj.id
                                                           if supported_file_types_obj else None)

        sharing_status_obj = content_model.metadata.supported_sharing_statuses
        sharing_status_obj_form = \
            SupportedSharingStatusForm(instance=sharing_status_obj,
                                       res_short_id=content_model.short_id,
                                       element_id=sharing_status_obj.id
                                       if sharing_status_obj else None)

        tool_icon_obj = content_model.metadata.app_icon
        tool_icon_form = ToolIconForm(instance=tool_icon_obj,
                                      res_short_id=content_model.short_id,
                                      element_id=tool_icon_obj.id
                                      if tool_icon_obj else None)

        ext_md_layout = Layout(
                HTML('<div class="form-group col-lg-6 col-xs-12" id="SupportedResTypes"> '
                     '{% load crispy_forms_tags %} '
                     '{% crispy supported_res_types_form %} '
                     '</div> '),
                HTML('<div class="form-group col-lg-6 col-xs-12" id="SupportedFileTypes"> '
                     '{% load crispy_forms_tags %} '
                     '{% crispy supported_file_types_form %} '
                     '</div> '),
                HTML('<div class="form-group col-lg-6 col-xs-12" id="SupportedSharingStatus"> '
                     '{% load crispy_forms_tags %} '
                     '{% crispy sharing_status_obj_form %} '
                     '</div> '),
                HTML("<div class='form-group col-lg-6 col-xs-12' id='homepage_url'> "
                     '{% load crispy_forms_tags %} '
                     '{% crispy homepage_url_form %} '
                     '</div>'),
                HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases'> "
                     '{% load crispy_forms_tags %} '
                     '{% crispy url_base_form %} '
                     '</div>'),
                HTML('<div class="form-group col-lg-6 col-xs-12" id="version"> '
                     '{% load crispy_forms_tags %} '
                     '{% crispy version_form %} '
                     '</div> '),
                HTML('<div class="form-group col-lg-6 col-xs-12" id="tool_icon"> '
                     '{% load crispy_forms_tags %} '
                     '{% crispy tool_icon_form %} '
                     '</div> '),
        )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)
        context['url_base_form'] = url_base_form
        context['homepage_url_form'] = homepage_url_form
        context['version_form'] = version_form
        context['supported_res_types_form'] = supported_res_types_form
        context['supported_file_types_form'] = supported_file_types_form
        context['tool_icon_form'] = tool_icon_form
        context['sharing_status_obj_form'] = sharing_status_obj_form

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
