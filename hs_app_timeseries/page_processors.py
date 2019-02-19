from django.contrib import messages

from mezzanine.pages.page_processors import processor_for

from crispy_forms.layout import Layout, HTML

from forms import UpdateSQLiteLayout, SeriesSelectionLayout, TimeSeriesMetaDataLayout, \
    UTCOffSetLayout, UTCOffSetForm
from hs_core import page_processors
from hs_core.views import add_generic_context
from hs_app_timeseries.models import TimeSeriesResource


@processor_for(TimeSeriesResource)
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)
    if content_model.metadata.is_dirty and content_model.can_update_sqlite_file:
        messages.info(request, "SQLite file is out of sync with metadata changes.")

    extended_metadata_exists = False
    if content_model.metadata.sites or \
            content_model.metadata.variables or \
            content_model.metadata.methods or \
            content_model.metadata.processing_levels or \
            content_model.metadata.time_series_results:
        extended_metadata_exists = True

    series_ids = content_model.metadata.series_ids_with_labels
    if 'series_id' in request.GET:
        selected_series_id = request.GET['series_id']
        if selected_series_id not in series_ids.keys():
            # this will happen only in case of CSV file upload when data is written
            # first time to the blank sqlite file as the series ids get changed to
            # uuids
            selected_series_id = series_ids.keys()[0]
        if 'series_id' in request.session:
            if selected_series_id != request.session['series_id']:
                request.session['series_id'] = selected_series_id
        else:
            request.session['series_id'] = selected_series_id
    else:
        selected_series_id = series_ids.keys()[0] if series_ids.keys() else None
        request.session['series_id'] = selected_series_id

    ts_result_value_count = None
    if content_model.metadata.series_names and selected_series_id is not None:
        sorted_series_names = sorted(content_model.metadata.series_names)
        selected_series_name = sorted_series_names[int(selected_series_id)]
        ts_result_value_count = int(content_model.metadata.value_counts[selected_series_name])

    # view depends on whether the resource is being edited
    if not edit_resource:
        # resource in VIEW Mode
        context = _get_resource_view_context(page, request, content_model, selected_series_id,
                                             series_ids, extended_metadata_exists)
    else:
        # resource in EDIT Mode
        context = _get_resource_edit_context(page, request, content_model, selected_series_id,
                                             series_ids, ts_result_value_count,
                                             extended_metadata_exists)

    # TODO: can we refactor to make it impossible to skip adding the generic context
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context


def _get_resource_view_context(page, request, content_model, selected_series_id, series_ids,
                               extended_metadata_exists):
    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=False,
                                               extended_metadata_layout=None, request=request)

    context['extended_metadata_exists'] = extended_metadata_exists
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['sites'] = [site for site in content_model.metadata.sites if selected_series_id in
                        site.series_ids]
    context['variables'] = [variable for variable in content_model.metadata.variables if
                            selected_series_id in variable.series_ids]
    context['methods'] = [method for method in content_model.metadata.methods if
                          selected_series_id in method.series_ids]
    context['processing_levels'] = [pro_level for pro_level in
                                    content_model.metadata.processing_levels if
                                    selected_series_id in pro_level.series_ids]
    context['timeseries_results'] = [ts_result for ts_result in
                                     content_model.metadata.time_series_results if
                                     selected_series_id in ts_result.series_ids]
    context['utc_offset'] = content_model.metadata.utc_offset.value if \
        content_model.metadata.utc_offset else None

    return context


def _get_resource_edit_context(page, request, content_model, selected_series_id, series_ids,
                               ts_result_value_count, extended_metadata_exists):

    from hs_file_types.models.timeseries import create_site_form, create_variable_form, \
        create_method_form, create_processing_level_form, create_timeseries_result_form

    utcoffset_form = None
    if content_model.has_csv_file:
        utc_offset = content_model.metadata.utc_offset
        utcoffset_form = UTCOffSetForm(instance=utc_offset,
                                       res_short_id=content_model.short_id,
                                       element_id=utc_offset.id if utc_offset else None,
                                       selected_series_id=selected_series_id)
    # create timeseries specific metadata element forms
    site_form = create_site_form(target=content_model, selected_series_id=selected_series_id)
    variable_form = create_variable_form(target=content_model,
                                         selected_series_id=selected_series_id)
    method_form = create_method_form(target=content_model, selected_series_id=selected_series_id)
    processing_level_form = create_processing_level_form(target=content_model,
                                                         selected_series_id=selected_series_id)

    timeseries_result_form = create_timeseries_result_form(target=content_model,
                                                           selected_series_id=selected_series_id)

    ext_md_layout = Layout(UpdateSQLiteLayout,
                           SeriesSelectionLayout,
                           TimeSeriesMetaDataLayout,
                           UTCOffSetLayout)

    if content_model.files.all().count() == 0:
        ext_md_layout = Layout(HTML("""<div class="alert alert-warning"><strong>No resource
        specific metadata is available. Add an ODM2 SQLite file or CSV file to see
        metadata.</strong></div>"""))

    # get the context from hs_core
    context = page_processors.get_page_context(page, request.user, resource_edit=True,
                                               extended_metadata_layout=ext_md_layout,
                                               request=request)

    # customize base context
    context['extended_metadata_exists'] = extended_metadata_exists
    context['resource_type'] = 'Time Series Resource'
    context['selected_series_id'] = selected_series_id
    context['series_ids'] = series_ids
    context['utcoffset_form'] = utcoffset_form
    context['site_form'] = site_form
    context['variable_form'] = variable_form
    context['method_form'] = method_form
    context['processing_level_form'] = processing_level_form
    context['timeseries_result_form'] = timeseries_result_form
    return context


def _get_series_label(series_id, resource):
    label = "{site_code}:{site_name}, {variable_code}:{variable_name}, {units_name}, " \
            "{pro_level_code}, {method_name}"
    site = [site for site in resource.metadata.sites if series_id in site.series_ids][0]
    variable = [variable for variable in resource.metadata.variables if
                series_id in variable.series_ids][0]
    method = [method for method in resource.metadata.methods if series_id in method.series_ids][0]
    pro_level = [pro_level for pro_level in resource.metadata.processing_levels if
                 series_id in pro_level.series_ids][0]
    ts_result = [ts_result for ts_result in resource.metadata.time_series_results if
                 series_id in ts_result.series_ids][0]
    label = label.format(site_code=site.site_code, site_name=site.site_name,
                         variable_code=variable.variable_code,
                         variable_name=variable.variable_name, units_name=ts_result.units_name,
                         pro_level_code=pro_level.processing_level_code,
                         method_name=method.method_name)
    return label


def _get_element_update_form_action(element_name, resource_id, element_id):
    action = "/hsapi/_internal/{}/{}/{}/update-metadata/"
    return action.format(resource_id, element_name, element_id)
