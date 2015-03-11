__author__ = 'pabitra'
from mezzanine.pages.page_processors import processor_for
from models import TimeSeriesResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors
from hs_core.views import add_dublin_core


@processor_for(TimeSeriesResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    if not edit_resource:
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None)
        extended_metadata_exists = False
        if content_model.metadata.site or \
                content_model.metadata.variable or \
                content_model.metadata.method or \
                content_model.metadata.processing_level or \
                content_model.metadata.time_series_result:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['site'] = content_model.metadata.site
        context['variable'] = content_model.metadata.variable
        context['method'] = content_model.metadata.method
        context['processing_level'] = content_model.metadata.processing_level
        context['timeseries_result'] = content_model.metadata.time_series_result
    else:
        site_form = SiteForm(instance=content_model.metadata.site, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.site.id if content_model.metadata.site else None)

        variable_form = VariableForm(instance=content_model.metadata.variable, res_short_id=content_model.short_id,
                             element_id=content_model.metadata.variable.id if content_model.metadata.variable else None)

        method_form = MethodForm(instance=content_model.metadata.method, res_short_id=content_model.short_id,
                                 element_id=content_model.metadata.method.id if content_model.metadata.method else None)

        processing_level_form = ProcessingLevelForm(instance=content_model.metadata.processing_level,
                                                    res_short_id=content_model.short_id,
                                                    element_id=content_model.metadata.processing_level.id
                                                    if content_model.metadata.processing_level else None)

        timeseries_result_form = TimeSeriesResultForm(instance=content_model.metadata.time_series_result,
                                                      res_short_id=content_model.short_id,
                                                      element_id=content_model.metadata.time_series_result.id
                                                      if content_model.metadata.time_series_result else None)
        ext_md_layout = Layout(
                                AccordionGroup('Site (required)',
                                    HTML("<div class='form-group' id='site'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy site_form %} '
                                     '</div>'),
                                ),

                                AccordionGroup('Variable (required)',
                                     HTML('<div class="form-group" id="variable"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy variable_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Method (required)',
                                     HTML('<div class="form-group" id="method"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy method_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Processing Level (required)',
                                     HTML('<div class="form-group" id="processinglevel"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy processing_level_form %} '
                                     '</div> '),
                                ),

                                AccordionGroup('Time Series Result (required)',
                                     HTML('<div class="form-group" id="timeseriesresult"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy timeseries_result_form %} '
                                     '</div> '),
                                ),
                        )


        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'Time Series Resource'
        context['site_form'] = site_form
        context['variable_form'] = variable_form
        context['method_form'] = method_form
        context['processing_level_form'] = processing_level_form
        context['timeseries_result_form'] = timeseries_result_form

    dublin_core_context = add_dublin_core(request, page)
    context.update(dublin_core_context)

    return context

# @processor_for(TimeSeriesResource)
# def ts_add_dublin_core(request, page):
#     return add_dublin_core(request, page)