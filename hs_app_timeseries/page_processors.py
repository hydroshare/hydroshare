__author__ = 'hydro'
from mezzanine.pages.page_processors import processor_for
from models import TimeSeriesResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from forms import *
from hs_core import page_processors

@processor_for(TimeSeriesResource)
def landing_page(request, page):
    content_model = page.get_content_model()
    if request.method == 'POST':
        pass
    #     site_form = SiteForm(request.POST)
    #     variable_form = VariableForm(request.POST)
    #     method_form = MethodForm(request.POST)
    #     proc_level_form = ProcessingLevelForm(request.POST)
    #     time_series_res_form = TimeSeriesResultForm(request.POST)
    #     if site_form.is_valid() and variable_form.is_valid() and method_form.is_valid() and proc_level_form.is_valid() \
    #             and time_series_res_form.is_valid():
    #         # TODO: do we know that we are creating a resource and not updating a resource
    #         content_model.metadata.create_element('site', site_form.cleaned_data)
    #         content_model.metadata.create_element('variable', variable_form.cleaned_data)
    #         content_model.metadata.create_element('method', method_form.cleaned_data)
    #         content_model.metadata.create_element('processinglevel', proc_level_form.cleaned_data)
    #         content_model.metadata.create_element('timeseriesresult', time_series_res_form.cleaned_data)
    #         content_model.save()
    else:
        # TODO: these forms need to be created with initial data
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
                                HTML("<div class='form-group' id='site'> "
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy site_form %} '
                                     '</div>'
                                     '<div class="form-group" id="variable"> '
                                        '{% crispy variable_form %} '
                                     '</div> '
                                     '<div class="form-group" id="method"> '
                                        '{% crispy method_form %} '
                                     '</div> '
                                     '<div class="form-group" id="processinglevel"> '
                                        '{% crispy processing_level_form %} '
                                     '</div> '
                                     '<div class="form-group" id="timeseriesresult"> '
                                        '{% crispy timeseries_result_form %} '
                                     '</div> '
                                ),
                        )


        context = page_processors.get_page_context(page, extended_metadata_layout=ext_md_layout)

        context['resource_type'] = 'Time Series Resource'
        context['site_form'] = site_form
        context['variable_form'] = variable_form
        context['method_form'] = method_form
        context['processing_level_form'] = processing_level_form
        context['timeseries_result_form'] = timeseries_result_form
        #context['cm'] = content_model
        return context


        # site_form = SiteForm()
        # variable_form = VariableForm()
        # method_form = MethodForm()
        # proc_level_form = ProcessingLevelForm()
        # time_series_res_form = TimeSeriesResultForm()
        # return {'site_form': site_form, 'variable_form': variable_form, 'method_form': method_form,
        #         'proc_level_form': proc_level_form, 'time_series_res_form': time_series_res_form}