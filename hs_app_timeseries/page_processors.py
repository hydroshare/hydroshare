from functools import partial, wraps

from django.forms.models import formset_factory
from django.forms import BaseFormSet

from forms import *
from hs_core import page_processors
from hs_core.views import *

@processor_for(TimeSeriesResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    series_ids = {}
    for result in content_model.metadata.time_series_results:
        for series_id in result.series_ids:
            series_ids[series_id] = _get_series_label(series_id, content_model)

    if 'series_id' in request.GET:
        selected_series_id = request.GET['series_id']
    else:
        selected_series_id = series_ids.keys()[0]

    # view depends on whether the resource is being edited
    if not edit_resource:
        # resource in VIEW Mode
        context = _get_resource_view_context(page, request, content_model, selected_series_id, series_ids)
    else:
        # resource in EDIT Mode
        context = _get_resource_edit_context(page, request, content_model, selected_series_id, series_ids)

    # TODO: can we refactor to make it impossible to skip adding the generic context
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context


def _get_resource_view_context(page, request, content_model, selected_series_id, series_ids):
    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=False,
                                               extended_metadata_layout=None, request=request)
    extended_metadata_exists = False
    if content_model.metadata.sites or \
            content_model.metadata.variables or \
            content_model.metadata.methods or \
            content_model.metadata.processing_levels or \
            content_model.metadata.time_series_results:
        extended_metadata_exists = True

    context['extended_metadata_exists'] = extended_metadata_exists,
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['sites'] = [site for site in content_model.metadata.sites if selected_series_id in site.series_ids]
    context['variables'] = [variable for variable in content_model.metadata.variables if selected_series_id in variable.series_ids]
    context['methods'] = [method for method in content_model.metadata.methods if selected_series_id in method.series_ids]
    context['processing_levels'] = [pro_level for pro_level in content_model.metadata.processing_levels if selected_series_id in pro_level.series_ids]
    context['timeseries_results'] = [ts_result for ts_result in content_model.metadata.time_series_results if selected_series_id in ts_result.series_ids]
    return context


def _get_resource_edit_context(page, request, content_model, selected_series_id, series_ids):
    SiteFormSetEdit = formset_factory(wraps(SiteForm)(partial(SiteForm, allow_edit=True)),
                                      formset=BaseFormSet, extra=0)

    sites = content_model.metadata.sites.filter(series_ids__contains=[selected_series_id])
    site_formset = SiteFormSetEdit(initial=sites.values(), prefix='site')

    for form in site_formset.forms:
        if len(form.initial) > 0:
            form.action = _get_element_update_form_action('site', content_model.short_id,
                                                          form.initial['id'])
            form.number = form.initial['id']

    VariableFormSetEdit = formset_factory(wraps(VariableForm)(partial(VariableForm, allow_edit=True)),
                                          formset=BaseFormSet, extra=0)
    variables = content_model.metadata.variables.filter(series_ids__contains=[selected_series_id])
    variable_formset = VariableFormSetEdit(initial=variables.values(), prefix='variable')

    for form in variable_formset.forms:
        if len(form.initial) > 0:
            form.action = _get_element_update_form_action('variable', content_model.short_id,
                                                          form.initial['id'])
            form.number = form.initial['id']

    MethodFormSetEdit = formset_factory(wraps(MethodForm)(partial(MethodForm, allow_edit=True)),
                                        formset=BaseFormSet, extra=0)
    methods = content_model.metadata.methods.filter(series_ids__contains=[selected_series_id])
    method_formset = MethodFormSetEdit(initial=methods.values(), prefix='method')

    for form in method_formset.forms:
        if len(form.initial) > 0:
            form.action = _get_element_update_form_action('method', content_model.short_id,
                                                          form.initial['id'])
            form.number = form.initial['id']

    ProcessingLevelFormSetEdit = formset_factory(wraps(ProcessingLevelForm)(partial(ProcessingLevelForm,
                                                                                    allow_edit=True)),
                                                 formset=BaseFormSet, extra=0)
    processing_levels = content_model.metadata.processing_levels.filter(series_ids__contains=[selected_series_id])
    processing_level_formset = ProcessingLevelFormSetEdit(initial=processing_levels.values(),
                                                          prefix='processing_level')

    for form in processing_level_formset.forms:
        if len(form.initial) > 0:
            form.action = _get_element_update_form_action('processinglevel', content_model.short_id,
                                                          form.initial['id'])
            form.number = form.initial['id']

    TimeSeriesResultFormSetEdit = formset_factory(wraps(TimeSeriesResultForm)(partial(TimeSeriesResultForm,
                                                                                      allow_edit=True)),
                                                  formset=BaseFormSet, extra=0)
    time_series_results = content_model.metadata.time_series_results.filter(series_ids__contains=[selected_series_id])
    timeseries_result_formset = TimeSeriesResultFormSetEdit(
        initial=time_series_results.values(), prefix='timeseriesresult')

    for form in timeseries_result_formset.forms:
        if len(form.initial) > 0:
            form.action = _get_element_update_form_action('timeseriesresult', content_model.short_id,
                                                          form.initial['id'])
            form.number = form.initial['id']

    ext_md_layout = Layout(SeriesSelectionLayout,
                           SiteLayoutEdit,
                           VariableLayoutEdit,
                           MethodLayoutEdit,
                           ProcessingLevelLayoutEdit,
                           TimeSeriesResultLayoutEdit
                          )

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=True,
                                               extended_metadata_layout=ext_md_layout, request=request)

    # customize base context
    context['resource_type'] = 'Time Series Resource'
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['site_formset'] = site_formset
    context['variable_formset'] = variable_formset
    context['method_formset'] = method_formset
    context['processing_level_formset'] = processing_level_formset
    context['timeseries_result_formset'] = timeseries_result_formset
    return context


def _get_series_label(series_id, resource):
    label = "(Site:{}, Variable:{}, Method:{})"
    site = [site for site in resource.metadata.sites if series_id in site.series_ids][0]
    variable = [variable for variable in resource.metadata.variables if series_id in variable.series_ids][0]
    method = [method for method in resource.metadata.methods if series_id in method.series_ids][0]
    label = label.format(site.site_code, variable.variable_name, method.method_type)
    return label


def _get_element_update_form_action(element_name, resource_id, element_id):
    action = "/hsapi/_internal/{}/{}/{}/update-metadata/"
    return action.format(resource_id, element_name, element_id)


