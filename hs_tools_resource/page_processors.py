__author__ = 'Drew, Jeff & Shaun'
from mezzanine.pages.page_processors import processor_for
from models import *
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from hs_core.forms import MetaDataElementDeleteForm
from django.forms.models import formset_factory
from functools import *
from hs_core.views import *

@processor_for(ToolResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
        extended_metadata_exists = False
        if content_model.metadata.url_bases.first() or \
                content_model.metadata.supported_res_types.first():
            extended_metadata_exists = True


        context['extended_metadata_exists'] = extended_metadata_exists
        context['url_base'] = content_model.metadata.url_bases.first()
        # context['res_types'] = content_model.metadata.res_types.all()
        context['supported_res_types'] = content_model.metadata.supported_res_types.first().get_supported_res_types_str() if  content_model.metadata.supported_res_types.first() else None
        context['version'] = content_model.metadata.versions.first()
    else:
        url_base = content_model.metadata.url_bases.first()
        if not url_base:
        #     url_base.update(element_id=url_base.id, resShortID=content_model.short_id, value=url_base.value)
        # else:
            url_base = RequestUrlBase.create(content_object=content_model.metadata,resShortID=content_model.short_id, value="")
        url_base_form = UrlBaseForm(instance=url_base,
                                    res_short_id=content_model.short_id,
                                    element_id=url_base.id
                                    if url_base else None,
                                    )

        # res_type = content_model.metadata.res_types.first()
        # res_type_form = ResTypeForm(instance=res_type,
        #                             res_short_id=content_model.short_id,
        #                             element_id=res_type.id
        #                             if res_type else None)


        version = content_model.metadata.versions.first()
        version_form = VersionForm(instance=version,
                                   res_short_id=content_model.short_id,
                                   element_id=version.id
                                   if version else None)

        supported_res_types_obj=content_model.metadata.supported_res_types.first()
        supported_res_types_form = SupportedResTypesForm(instance=supported_res_types_obj, res_short_id=content_model.short_id,
                             element_id=supported_res_types_obj.id if supported_res_types_obj else None)

        ext_md_layout = Layout(
                                 # AccordionGroup('Model Output (required)',
                                HTML('<div class="form-group" id="SupportedResTypes"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy supported_res_types_form %} '
                                 '</div> '),
                                # ),

                                HTML("<div class='form-group col-lg-6 col-xs-12' id='url_bases'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy url_base_form %} '
                                     '</div>'),
                                #
                                # HTML("<div class='form-group col-lg-6 col-xs-12' id='res_types'> "
                                #         '{% load crispy_forms_tags %} '
                                #         '{% crispy res_type_form %} '
                                #      '</div>'),
                                #
                                HTML('<div class="form-group col-lg-6 col-xs-12" id="version"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy version_form %} '
                                     '</div> '),


                        )


        # get tresource_typehe context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout, request=request)

        res_type_names = []
        for res_type_class in get_resource_types():
            res_type_names.append(res_type_class.__name__)

        context[''] = 'Tool Resource'
        context['url_base_form'] = url_base_form
        # context['res_type_form'] = res_type_form
        context['version_form'] = version_form
        # context['res_types'] = res_type_names
        context['supported_res_types_form'] = supported_res_types_form

        if content_model.metadata.supported_res_types.first():
            supported_res_types = content_model.metadata.supported_res_types.first().supported_res_types.all()
            checked_res_str=""
            if len(supported_res_types) > 0:
                for parameter in supported_res_types:
                    checked_res_str+=str(parameter.description)
                    checked_res_str+=","

            context['checked_res'] = checked_res_str
    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
