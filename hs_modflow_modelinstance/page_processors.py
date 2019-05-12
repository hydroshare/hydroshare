from functools import partial, wraps

from crispy_forms.layout import Layout, HTML
from django.forms import formset_factory
from django.http import HttpResponseRedirect
from mezzanine.pages.page_processors import processor_for

from hs_core import page_processors
from hs_core.forms import BaseFormSet, MetaDataElementDeleteForm
from hs_core.views import add_generic_context
from hs_modflow_modelinstance.forms import ModelOutputForm, ExecutedByForm, StudyAreaForm, \
    GridDimensionsForm, StressPeriodForm, GroundWaterFlowForm, BoundaryConditionForm, \
    ModelCalibrationForm, ModelInputForm, GeneralElementsForm, ModelInputLayoutEdit, \
    ModalDialogLayoutAddModelInput
from hs_modflow_modelinstance.models import MODFLOWModelInstanceResource


@processor_for(MODFLOWModelInstanceResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page,
                                                   request.user,
                                                   request=request,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=None)
        if isinstance(context, HttpResponseRedirect):
            # sending user to login page
            return context

        extended_metadata_exists = False
        if content_model.metadata.model_output or \
                content_model.metadata.executed_by or \
                content_model.metadata.study_area or \
                content_model.metadata.grid_dimensions or \
                content_model.metadata.stress_period or \
                content_model.metadata.ground_water_flow or \
                content_model.metadata.boundary_condition or \
                content_model.metadata.model_calibration or \
                content_model.metadata.model_inputs or \
                content_model.metadata.general_elements:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['model_output'] = content_model.metadata.model_output
        context['executed_by'] = content_model.metadata.executed_by
        context['study_area'] = content_model.metadata.study_area
        context['grid_dimensions'] = content_model.metadata.grid_dimensions
        context['stress_period'] = content_model.metadata.stress_period
        context['ground_water_flow'] = content_model.metadata.ground_water_flow
        context['boundary_condition'] = content_model.metadata.boundary_condition
        context['model_calibration'] = content_model.metadata.model_calibration
        context['model_inputs'] = content_model.metadata.model_inputs
        context['general_elements'] = content_model.metadata.general_elements

    # add MODFLOW Model parameters context
    else:
        model_output_form = ModelOutputForm(instance=content_model.metadata.model_output,
                                            res_short_id=content_model.short_id,
                                            element_id=content_model.metadata.model_output.id
                                            if content_model.metadata.model_output else None)

        executed_by_form = ExecutedByForm(instance=content_model.metadata.executed_by,
                                          res_short_id=content_model.short_id,
                                          element_id=content_model.metadata.executed_by.id
                                          if content_model.metadata.executed_by else None)

        study_area_form = StudyAreaForm(instance=content_model.metadata.study_area,
                                        res_short_id=content_model.short_id,
                                        element_id=content_model.metadata.study_area.id
                                        if content_model.metadata.study_area else None)

        grid_dimensions_form = GridDimensionsForm(
            instance=content_model.metadata.grid_dimensions,
            res_short_id=content_model.short_id,
            element_id=content_model.metadata.grid_dimensions.id
            if content_model.metadata.grid_dimensions else None)

        stress_period_form = StressPeriodForm(instance=content_model.metadata.stress_period,
                                              res_short_id=content_model.short_id,
                                              element_id=content_model.metadata.stress_period.id
                                              if content_model.metadata.stress_period else None)

        ground_water_flow_form = GroundWaterFlowForm(
            instance=content_model.metadata.ground_water_flow,
            res_short_id=content_model.short_id,
            element_id=content_model.metadata.ground_water_flow.id
            if content_model.metadata.ground_water_flow else None)

        boundary_condition_form = BoundaryConditionForm(
            instance=content_model.metadata.boundary_condition,
            res_short_id=content_model.short_id,
            element_id=content_model.metadata.boundary_condition.id
            if content_model.metadata.boundary_condition else None)

        model_calibration_form = ModelCalibrationForm(
            instance=content_model.metadata.model_calibration,
            res_short_id=content_model.short_id,
            element_id=content_model.metadata.model_calibration.id
            if content_model.metadata.model_calibration else None)

        ModelInputFormSetEdit = formset_factory(wraps(ModelInputForm)(partial(ModelInputForm,
                                                                              allow_edit=True)),
                                                formset=BaseFormSet, extra=0)
        model_input_formset = ModelInputFormSetEdit(
            initial=content_model.metadata.model_inputs.values(),
            prefix='modelinput')
        for model_input_form in model_input_formset.forms:
            if len(model_input_form.initial) > 0:
                model_input_form.action = "/hsapi/_internal/%s/modelinput/%s/update-metadata/" % \
                                          (content_model.short_id, model_input_form.initial['id'])
                model_input_form.delete_modal_form = MetaDataElementDeleteForm(
                    content_model.short_id, 'modelinput',
                    model_input_form.initial['id'])
                model_input_form.number = model_input_form.initial['id']
            else:
                model_input_form.action = "/hsapi/_internal/%s/modelinput/add-metadata/" % \
                                          content_model.short_id

        add_modelinput_modal_form = ModelInputForm(allow_edit=False,
                                                   res_short_id=content_model.short_id)

        general_elements_form = GeneralElementsForm(
            instance=content_model.metadata.general_elements,
            res_short_id=content_model.short_id,
            element_id=content_model.metadata.general_elements.id
            if content_model.metadata.general_elements else None)

        ext_md_layout = Layout(HTML("<div class='col-xs-12 col-sm-6'>"
                                    "<div class='form-group' id='modeloutput'> "
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_output_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="executedby"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy executed_by_form %} '
                                    '</div> '),

                               HTML('<div class="form-group" id="boundarycondition"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy boundary_condition_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="generalelements"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy general_elements_form %} '
                                    '</div>'),
                               HTML("</div>"),

                               ModelInputLayoutEdit,

                               ModalDialogLayoutAddModelInput,

                               HTML('<div class="col-xs-12 col-sm-6">'
                                    '<div class="form-group" id="studyarea"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy study_area_form %} '
                                    '</div> '),

                               HTML('<div class="form-group" id="griddimensions"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy grid_dimensions_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="stressperiod"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy stress_period_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="groundwaterflow"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy ground_water_flow_form %} '
                                    '</div>'),

                               HTML('<div class="form-group" id="modelcalibration"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy model_calibration_form %} '
                                    '</div></div>')
                               )

        # get the context from hs_core
        context = page_processors.get_page_context(page,
                                                   request.user,
                                                   resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout,
                                                   request=request)

        context['resource_type'] = 'MODFLOW Model Instance Resource'
        context['model_output_form'] = model_output_form
        context['executed_by_form'] = executed_by_form
        context['study_area_form'] = study_area_form
        context['grid_dimensions_form'] = grid_dimensions_form
        context['stress_period_form'] = stress_period_form
        context['ground_water_flow_form'] = ground_water_flow_form
        context['boundary_condition_form'] = boundary_condition_form
        context['model_calibration_form'] = model_calibration_form
        context['model_input_formset'] = model_input_formset
        context['add_modelinput_modal_form'] = add_modelinput_modal_form
        context['general_elements_form'] = general_elements_form

    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
