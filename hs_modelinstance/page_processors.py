__author__ = 'Mohamed'
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from hs_modelinstance.models import ModelInstanceResource
from hs_modelinstance.forms import ModelOutputForm, ExecutedByForm

from mezzanine.pages.page_processors import processor_for

@processor_for(ModelInstanceResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, request=request, resource_edit=edit_resource,
                                                   extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.model_output or \
                content_model.metadata.executed_by:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['model_output'] = content_model.metadata.model_output
        context['executed_by'] = content_model.metadata.executed_by
    else:
        model_output_form = ModelOutputForm(instance=content_model.metadata.model_output,
                                            res_short_id=content_model.short_id,
                                            element_id=content_model.metadata.model_output.id if content_model.metadata.model_output else None)

        executed_by_form = ExecutedByForm(instance=content_model.metadata.executed_by,
                                          res_short_id=content_model.short_id,
                                          element_id=content_model.metadata.executed_by.id if content_model.metadata.executed_by else None)

        ext_md_layout = Layout(
                           HTML("<div class='form-group' id='modeloutput'> "
                                '{% load crispy_forms_tags %} '
                                '{% crispy model_output_form %} '
                                '</div>'),
                           HTML('<div class="form-group" id="executedby"> '
                                '{% load crispy_forms_tags %} '
                                '{% crispy executed_by_form %} '
                                '</div> ')
        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout, request=request)

        context['resource_type'] = 'Model Instance Resource'
        context['model_output_form'] = model_output_form
        context['executed_by_form'] = executed_by_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
