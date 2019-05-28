from crispy_forms.layout import Layout, HTML
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for

from forms import AppHomePageUrlForm, TestingProtocolUrlForm, HelpPageUrlForm, \
    SourceCodeUrlForm, IssuesPageUrlForm, MailingListUrlForm, RoadmapForm, \
    VersionForm, SupportedResTypesForm, SupportedAggTypesForm, \
    SupportedSharingStatusForm, ToolIconForm, UrlBaseForm, SupportedFileExtensionsForm, \
    UrlBaseAggregationForm, UrlBaseFileForm
from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_file_types.utils import get_SupportedAggTypes_choices
from models import ToolResource
from utils import get_SupportedResTypes_choices


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
        if isinstance(context, HttpResponseRedirect):
            # sending user to login page
            return context
        extended_metadata_exists = False
        if content_model.metadata.url_base or content_model.metadata.version:
            extended_metadata_exists = True

        new_supported_res_types_array = []
        if content_model.metadata.supported_resource_types:
            extended_metadata_exists = True
            supported_res_types_str = content_model.metadata. \
                supported_resource_types.get_supported_res_types_str()
            supported_res_types_array = supported_res_types_str.split(',')
            for type_name in supported_res_types_array:
                for class_verbose_list in get_SupportedResTypes_choices():
                    if type_name.lower() == class_verbose_list[0].lower():
                        new_supported_res_types_array += [class_verbose_list[1]]
                        break

            context['supported_res_types'] = ", ".join(new_supported_res_types_array)

        new_supported_agg_types_array = []
        if content_model.metadata.supported_aggregation_types:
            extended_metadata_exists = True
            supported_agg_types_str = content_model.metadata. \
                supported_aggregation_types.get_supported_agg_types_str()
            supported_agg_types_array = supported_agg_types_str.split(',')
            for type_name in supported_agg_types_array:
                for class_verbose_list in get_SupportedAggTypes_choices():
                    if type_name.lower() == class_verbose_list[0].lower():
                        new_supported_agg_types_array += [class_verbose_list[1]]
                        break

            context['supported_agg_types'] = ", ".join(new_supported_agg_types_array)

        if content_model.metadata.supported_sharing_status is not None:
            extended_metadata_exists = True
            sharing_status_str = content_model.metadata.supported_sharing_status \
                .get_sharing_status_str()
            context['supported_sharing_status'] = sharing_status_str

        if content_model.metadata.app_icon:
            context['tool_icon_url'] = content_model.metadata.app_icon.data_url

        if content_model.metadata.supported_file_extensions:
            context['supported_file_extensions'] = content_model.metadata.supported_file_extensions

        context['extended_metadata_exists'] = extended_metadata_exists

        context['url_base'] = content_model.metadata.url_base
        context['url_base_aggregation'] = content_model.metadata.url_base_aggregation
        context['url_base_file'] = content_model.metadata.url_base_file
        context['version'] = content_model.metadata.version
        context['homepage_url'] = content_model.metadata.app_home_page_url
        context['testing_protocol_url'] = content_model.metadata.testing_protocol_url.first()
        context['help_page_url'] = content_model.metadata.help_page_url.first()
        context['source_code_url'] = content_model.metadata.source_code_url.first()
        context['issues_page_url'] = content_model.metadata.issues_page_url.first()
        context['mailing_list_url'] = content_model.metadata.mailing_list_url.first()
        context['roadmap'] = content_model.metadata.roadmap.first()
        # context['show_on_open_with_list'] = content_model.metadata.show_on_open_with_list.first()

    else:
        url_base = content_model.metadata.url_base
        url_base_form = UrlBaseForm(instance=url_base,
                                    res_short_id=content_model.short_id,
                                    element_id=url_base.id
                                    if url_base else None)

        url_base_aggregation = content_model.metadata.url_base_aggregation
        url_base_aggregation_form = UrlBaseAggregationForm(instance=url_base_aggregation,
                                                           res_short_id=content_model.short_id,
                                                           element_id=url_base_aggregation.id
                                                           if url_base_aggregation else None)

        url_base_file = content_model.metadata.url_base_file
        url_base_file_form = UrlBaseFileForm(instance=url_base_file,
                                             res_short_id=content_model.short_id,
                                             element_id=url_base_file.id
                                             if url_base_file else None)

        supported_file_extensions = content_model.metadata.supported_file_extensions
        supported_file_extensions_form = \
            SupportedFileExtensionsForm(instance=supported_file_extensions,
                                        res_short_id=content_model.short_id,
                                        element_id=supported_file_extensions.id
                                        if supported_file_extensions else None)

        homepage_url = content_model.metadata.app_home_page_url
        homepage_url_form = \
            AppHomePageUrlForm(instance=homepage_url,
                               res_short_id=content_model.short_id,
                               element_id=homepage_url.id
                               if homepage_url else None)

        testing_protocol_url = content_model.metadata.testing_protocol_url.first()
        testing_protocol_url_form = TestingProtocolUrlForm(instance=testing_protocol_url,
                                                           res_short_id=content_model.short_id,
                                                           element_id=testing_protocol_url.id
                                                           if testing_protocol_url else None)

        help_page_url = content_model.metadata.help_page_url.first()
        help_page_url_form = HelpPageUrlForm(instance=help_page_url,
                                             res_short_id=content_model.short_id,
                                             element_id=help_page_url.id
                                             if help_page_url else None)

        source_code_url = content_model.metadata.source_code_url.first()
        source_code_url_form = SourceCodeUrlForm(instance=source_code_url,
                                                 res_short_id=content_model.short_id,
                                                 element_id=source_code_url.id
                                                 if source_code_url else None)

        issues_page_url = content_model.metadata.issues_page_url.first()
        issues_page_url_form = IssuesPageUrlForm(instance=issues_page_url,
                                                 res_short_id=content_model.short_id,
                                                 element_id=issues_page_url.id
                                                 if issues_page_url else None)

        mailing_list_url = content_model.metadata.mailing_list_url.first()
        mailing_list_url_form = MailingListUrlForm(instance=mailing_list_url,
                                                   res_short_id=content_model.short_id,
                                                   element_id=mailing_list_url.id
                                                   if mailing_list_url else None)

        roadmap = content_model.metadata.roadmap.first()
        roadmap_form = RoadmapForm(instance=roadmap,
                                   res_short_id=content_model.short_id,
                                   element_id=roadmap.id
                                   if roadmap else None)

        # show_on_open_with_list = content_model.metadata.show_on_open_with_list.first()
        # show_on_open_with_list_form = ShowOnOpenWithListForm(instance=show_on_open_with_list,
        #                                                      res_short_id=content_model.short_id,
        #                                                      element_id=show_on_open_with_list.id
        #                                                      if show_on_open_with_list else None)

        version = content_model.metadata.version
        version_form = VersionForm(instance=version,
                                   res_short_id=content_model.short_id,
                                   element_id=version.id
                                   if version else None)

        supported_res_types_obj = content_model.metadata.supported_resource_types
        supported_res_types_form = SupportedResTypesForm(instance=supported_res_types_obj,
                                                         res_short_id=content_model.short_id,
                                                         element_id=supported_res_types_obj.id
                                                         if supported_res_types_obj else None)

        supported_agg_types_obj = content_model.metadata.supported_aggregation_types
        supported_agg_types_form = SupportedAggTypesForm(instance=supported_agg_types_obj,
                                                         res_short_id=content_model.short_id,
                                                         element_id=supported_agg_types_obj.id
                                                         if supported_agg_types_obj else None)

        sharing_status_obj = content_model.metadata.supported_sharing_status
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
            HTML('<div class="form-group col-lg-6 col-xs-12" id="SupportedAggTypes"> '
                 '{% load crispy_forms_tags %} '
                 '{% crispy supported_agg_types_form %} '
                 '</div> '),
            HTML('<div class="form-group col-lg-6 col-xs-12" id="SupportedSharingStatus"> '
                 '{% load crispy_forms_tags %} '
                 '{% crispy sharing_status_obj_form %} '
                 '</div> '),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='supported_file_extensions'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy supported_file_extensions_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='homepage_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy homepage_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy url_base_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases_aggregation'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy url_base_aggregation_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases_file'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy url_base_file_form %} '
                 '</div>'),
            HTML('<div class="form-group col-lg-6 col-xs-12" id="version"> '
                 '{% load crispy_forms_tags %} '
                 '{% crispy version_form %} '
                 '</div> '),
            HTML('<div class="form-group col-lg-6 col-xs-12" id="tool_icon"> '
                 '{% load crispy_forms_tags %} '
                 '{% crispy tool_icon_form %} '
                 '</div> '),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='testing_protocol_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy testing_protocol_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='help_page_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy help_page_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='source_code_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy source_code_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='issues_page_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy issues_page_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='mailing_list_url'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy mailing_list_url_form %} '
                 '</div>'),
            HTML("<div class='form-group col-lg-6 col-xs-12' id='roadmap'> "
                 '{% load crispy_forms_tags %} '
                 '{% crispy roadmap_form %} '
                 '</div>'),
            # HTML("<div class='form-group col-lg-6 col-xs-12' id='show_on_open_with_list'> "
            #      '{% load crispy_forms_tags %} '
            #      '{% crispy show_on_open_with_list_form %} '
            #      '</div>'),
        )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)
        context['url_base_form'] = url_base_form
        context['url_base_aggregation_form'] = url_base_aggregation_form
        context['url_base_file_form'] = url_base_file_form
        context['supported_file_extensions_form'] = supported_file_extensions_form
        context['homepage_url_form'] = homepage_url_form
        context['version_form'] = version_form
        context['supported_res_types_form'] = supported_res_types_form
        context['supported_agg_types_form'] = supported_agg_types_form
        context['tool_icon_form'] = tool_icon_form
        context['sharing_status_obj_form'] = sharing_status_obj_form
        context['testing_protocol_url_form'] = testing_protocol_url_form
        context['help_page_url_form'] = help_page_url_form
        context['source_code_url_form'] = source_code_url_form
        context['issues_page_url_form'] = issues_page_url_form
        context['mailing_list_url_form'] = mailing_list_url_form
        context['roadmap_form'] = roadmap_form
        # context['show_on_open_with_list_form'] = show_on_open_with_list_form

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
