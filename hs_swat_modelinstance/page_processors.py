__author__ = 'Mohamed Morsy'
from mezzanine.pages.page_processors import processor_for
from hs_swat_modelinstance.models import SWATModelInstanceResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from hs_modelinstance.forms import *
from forms import *
from hs_core import page_processors
from hs_core.views import *

@processor_for(SWATModelInstanceResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.model_output or \
                content_model.metadata.executed_by or \
                content_model.metadata.model_objective or \
                content_model.metadata.simulation_type or \
                content_model.metadata.swat_model_parameters:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['model_output'] = content_model.metadata.model_output
        context['executed_by'] = content_model.metadata.executed_by
        context['model_objective'] = content_model.metadata.model_objective
        context['simulation_type'] = content_model.metadata.simulation_type
        context['swat_model_parameters'] = content_model.metadata.swat_model_parameters

        #add SWAT Model parameters context
    else:
        model_output_form = ModelOutputForm(instance=content_model.metadata.model_output, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_output.id if content_model.metadata.model_output else None)

        executed_by_form = ExecutedByForm(instance=content_model.metadata.executed_by, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.executed_by.id if content_model.metadata.executed_by else None)

        model_objective_form = modelObjectiveForm(instance=content_model.metadata.model_objective, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_objective.id if content_model.metadata.model_objective else None)

        simulation_type_form = simulationTypeForm(instance=content_model.metadata.simulation_type, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.simulation_type.id if content_model.metadata.simulation_type else None)

        swat_model_parameters_form = SWATmodelParametersForm(instance=content_model.metadata.swat_model_parameters, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.swat_model_parameters.id if content_model.metadata.swat_model_parameters else None)

        ext_md_layout = Layout(
                                AccordionGroup('Model Output (required)',
                                    HTML("<div class='form-group' id='modeloutput'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy model_output_form %} '
                                     '</div>'),
                                ),

                                AccordionGroup('Executed By (required)',
                                     HTML('<div class="form-group" id="executedby"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy executed_by_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Model Objective (required)',
                                     HTML('<div class="form-group" id="modelobjective"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy model_objective_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Simulation Type',
                                     HTML('<div class="form-group" id="simulationtype"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy simulation_type_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('SWAT Model Parameters (required)',
                                     HTML('<div class="form-group" id="swatmodelparameters"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy swat_model_parameters_form %} '
                                     '</div> '),
                                ),
                        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'SWAT Model Instance Resource'
        context['model_output_form'] = model_output_form
        context['executed_by_form'] = executed_by_form
        context['model_objective_form'] = model_objective_form
        context['simulation_type_form'] = simulation_type_form
        context['swat_model_parameters_form'] = swat_model_parameters_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context