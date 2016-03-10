__author__ = 'Mohamed Morsy'
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.layout import Layout, HTML

from hs_core import page_processors
from hs_core.views import add_generic_context

from hs_swat_modelinstance.models import SWATModelInstanceResource
from hs_swat_modelinstance.forms import ModelOutputForm, ExecutedByForm, ModelObjectiveForm,\
    SimulationTypeForm, ModelMethodForm, ModelParameterForm, ModelInputForm

from mezzanine.pages.page_processors import processor_for

@processor_for(SWATModelInstanceResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, request=request, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.model_output or \
                content_model.metadata.executed_by or \
                content_model.metadata.model_objective or \
                content_model.metadata.simulation_type or \
                content_model.metadata.model_method or \
                content_model.metadata.model_parameter or \
                content_model.metadata.model_input:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['model_output'] = content_model.metadata.model_output
        context['executed_by'] = content_model.metadata.executed_by
        context['model_objective'] = content_model.metadata.model_objective
        context['simulation_type'] = content_model.metadata.simulation_type
        context['model_method'] = content_model.metadata.model_method
        context['model_parameter'] = content_model.metadata.model_parameter
        context['model_input'] = content_model.metadata.model_input

        #add SWAT Model parameters context
    else:
        model_output_form = ModelOutputForm(instance=content_model.metadata.model_output, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_output.id if content_model.metadata.model_output else None)

        executed_by_form = ExecutedByForm(instance=content_model.metadata.executed_by, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.executed_by.id if content_model.metadata.executed_by else None)

        model_objective_form = ModelObjectiveForm(instance=content_model.metadata.model_objective, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_objective.id if content_model.metadata.model_objective else None)

        simulation_type_form = SimulationTypeForm(instance=content_model.metadata.simulation_type, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.simulation_type.id if content_model.metadata.simulation_type else None)

        model_method_form = ModelMethodForm(instance=content_model.metadata.model_method, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_method.id if content_model.metadata.model_method else None)

        model_parameter_form = ModelParameterForm(instance=content_model.metadata.model_parameter, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_parameter.id if content_model.metadata.model_parameter else None)

        model_input_form = ModelInputForm(instance=content_model.metadata.model_input, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.model_input.id if content_model.metadata.model_input else None)

        ext_md_layout = Layout(HTML("<div class='row'><div class='col-xs-12 col-sm-6'><div class='form-group' id='modeloutput'> "
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_output_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="executedby"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy executed_by_form %} '
                                    '</div> '),

                               HTML('<div class="form-group" id="modelobjective"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_objective_form %} '
                                    '</div> '),

                               HTML('<div class="form-group" id="simulationtype"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy simulation_type_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="modelmethod"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_method_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="modelparameter"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_parameter_form %} '
                                    '</div></div>'),

                               HTML('<div class="col-xs-12 col-sm-6"><div class="form-group" id="modelinput"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_input_form %} '
                                    '</div></div>'),

                        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout, request=request)

        context['resource_type'] = 'SWAT Model Instance Resource'
        context['model_output_form'] = model_output_form
        context['executed_by_form'] = executed_by_form
        context['model_objective_form'] = model_objective_form
        context['simulation_type_form'] = simulation_type_form
        context['model_method_form'] = model_method_form
        context['model_parameter_form'] = model_parameter_form
        context['model_input_form'] = model_input_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
