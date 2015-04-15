__author__ = 'Shaun'
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
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.url_bases.first() or \
                content_model.metadata.res_types.first():
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['url_base'] = content_model.metadata.url_bases.first()
        context['res_types'] = content_model.metadata.res_types.all()
        context['fees'] = content_model.metadata.fees.all()
        context['version'] = content_model.metadata.versions.first()
    else:
        url_base_form = UrlBaseForm(instance=content_model.metadata.url_bases.first(),
                                    res_short_id=content_model.short_id,
                                    element_id=content_model.metadata.url_bases.first().id
                                    if content_model.metadata.url_bases.first() else None)

        ResTypeFormSetEdit = formset_factory(wraps(ResTypeForm)(partial(ResTypeForm,
                                                                        allow_edit=edit_resource)),
                                             formset=BaseFormSet, extra=0)
        res_type_formset = ResTypeFormSetEdit(initial=content_model.metadata.res_types.all().values(),
                                              prefix='res_type')
        add_toolresourcetype_modal_form = ResTypeForm(allow_edit=edit_resource, res_short_id=content_model.short_id)

        for form in res_type_formset.forms:
            if len(form.initial) > 0:
                form.delete_modal_form = MetaDataElementDeleteForm(content_model.short_id,
                                                                   'toolresourcetype',
                                                                   form.initial['id'])
                form.action = "/hsapi/_internal/%s/toolresourcetype/%s/update-metadata/" % (content_model.short_id,
                                                                                            form.initial['id'])
                form.number = form.initial['id']
            else:
                form.action = "/hsapi/_internal/%s/toolresourcetype/add-metadata/" % content_model.short_id

        fees_form = FeeForm(instance=content_model.metadata.fees.first(),
                            res_short_id=content_model.short_id,
                            element_id=content_model.metadata.fees.first().id
                            if content_model.metadata.fees.first() else None)

        version_form = VersionForm(instance=content_model.metadata.versions.first(),
                                   res_short_id=content_model.short_id,
                                   element_id=content_model.metadata.versions.first().id
                                   if content_model.metadata.versions.first() else None)

        ext_md_layout = Layout(
                                AccordionGroup('Url Base (required)',
                                    HTML("<div class='form-group' id='url_bases'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy url_base_form %} '
                                     '</div>'),
                                ),

                                AccordionGroup('Resource Types (required)',
                                               ResTypeLayoutEdit),
                                ModalDialogLayoutAddResType,

                                AccordionGroup('Fees (optional)',
                                     HTML('<div class="form-group" id="fees"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy fees_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Version (optional)',
                                     HTML('<div class="form-group" id="version"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy version_form %} '
                                     '</div> '),
                                ),
                        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'Tool Resource'
        context['url_base_form'] = url_base_form
        context['res_types_formset'] = res_type_formset
        context['add_toolresourcetype_modal_form'] = add_toolresourcetype_modal_form
        context['fees_form'] = fees_form
        context['version_form'] = version_form

    hs_core_dublin_context = add_generic_context(request, page)
    context.update(hs_core_dublin_context)

    return context
