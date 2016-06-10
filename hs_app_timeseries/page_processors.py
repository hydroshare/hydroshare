from functools import partial, wraps

from django.forms.models import formset_factory
from django.forms import BaseFormSet

from forms import *
from hs_core import page_processors
from hs_core.views import *

@processor_for(TimeSeriesResource)
# TODO: problematic permissions
def landing_page(request, page):
    """
        A typical Mezzanine page processor.

        TODO: refactor to make it clear that there are two different modes = EDITABLE | READONLY
                - split into two helper functions: readonly_landing_page(...) and editable_landing_page(...)
    """
    content_model = page.get_content_model()
    edit_resource = page_processors.check_resource_mode(request)

    # view depends on whether the resource is being edited
    if not edit_resource:
        # READONLY
        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=None, request=request)
        extended_metadata_exists = False
        if content_model.metadata.sites or \
                content_model.metadata.variables or \
                content_model.metadata.methods or \
                content_model.metadata.processing_levels or \
                content_model.metadata.time_series_results:
            extended_metadata_exists = True

        context['extended_metadata_exists'] = extended_metadata_exists
        context['sites'] = content_model.metadata.sites
        context['variables'] = content_model.metadata.variables
        context['methods'] = content_model.metadata.methods
        context['processing_levels'] = content_model.metadata.processing_levels
        context['timeseries_results'] = content_model.metadata.time_series_results
    else:
        # EDIT MODE

        # add some forms
        SiteFormSetEdit = formset_factory(wraps(SiteForm)(partial(SiteForm, allow_edit=edit_resource)),
                                          formset=BaseFormSet, extra=0)
        site_formset = SiteFormSetEdit(initial=content_model.metadata.sites.values(), prefix='site')

        for form in site_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/site/%s/update-metadata/" % (content_model.short_id,
                                                                                form.initial['id'])
                form.number = form.initial['id']

        VariableFormSetEdit = formset_factory(wraps(VariableForm)(partial(VariableForm, allow_edit=edit_resource)),
                                                    formset=BaseFormSet, extra=0)
        variable_formset = VariableFormSetEdit(initial=content_model.metadata.variables.values(), prefix='variable')

        for form in variable_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/variable/%s/update-metadata/" % (content_model.short_id,
                                                                                    form.initial['id'])
                form.number = form.initial['id']

        MethodFormSetEdit = formset_factory(wraps(MethodForm)(partial(MethodForm, allow_edit=edit_resource)),
                                                  formset=BaseFormSet, extra=0)
        method_formset = MethodFormSetEdit(initial=content_model.metadata.methods.values(), prefix='method')

        for form in method_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/method/%s/update-metadata/" % (content_model.short_id,
                                                                                  form.initial['id'])
                form.number = form.initial['id']

        ProcessingLevelFormSetEdit = formset_factory(wraps(ProcessingLevelForm)(partial(ProcessingLevelForm,
                                                                                        allow_edit=edit_resource)),
                                                     formset=BaseFormSet, extra=0)
        processing_level_formset = ProcessingLevelFormSetEdit(initial=content_model.metadata.processing_levels.values(),
                                                              prefix='processing_level')

        for form in processing_level_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/processinglevel/%s/update-metadata/" % (content_model.short_id,
                                                                                           form.initial['id'])
                form.number = form.initial['id']

        TimeSeriesResultFormSetEdit = formset_factory(wraps(TimeSeriesResultForm)(partial(TimeSeriesResultForm,
                                                                                          allow_edit=edit_resource)),
                                                      formset=BaseFormSet, extra=0)
        timeseries_result_formset = TimeSeriesResultFormSetEdit(
            initial=content_model.metadata.time_series_results.values(),prefix='timeseriesresult')

        for form in timeseries_result_formset.forms:
            if len(form.initial) > 0:
                form.action = "/hsapi/_internal/%s/timeseriesresult/%s/update-metadata/" % (content_model.short_id,
                                                                                            form.initial['id'])
                form.number = form.initial['id']

        ext_md_layout = Layout(SiteLayoutEdit,
                               VariableLayoutEdit,
                               MethodLayoutEdit,
                               ProcessingLevelLayoutEdit,
                               TimeSeriesResultLayoutEdit
                              )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource,
                                                   extended_metadata_layout=ext_md_layout, request=request)

        # customize base context
        context['resource_type'] = 'Time Series Resource'
        context['site_formset'] = site_formset
        context['variable_formset'] = variable_formset
        context['method_formset'] = method_formset
        context['processing_level_formset'] = processing_level_formset
        context['timeseries_result_formset'] = timeseries_result_formset

    # TODO: can we refactor to make it impossible to skip adding the generic context
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
