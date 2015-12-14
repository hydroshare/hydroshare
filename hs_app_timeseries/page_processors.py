__author__ = 'pabitra'
from mezzanine.pages.page_processors import processor_for
from models import TimeSeriesResource
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
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
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=None, request=request)
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
        # EDIT MODE

        # add some forms
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
            HTML('<div class="form-group col-sm-6 col-xs-12">'
                     '<div id="site">'
                         '{% load crispy_forms_tags %} '
                         '{% crispy site_form %} '
                         '<hr style="border:0">'
                     '</div>'
                     '<div id="variable">'
                         '{% load crispy_forms_tags %} '
                         '{% crispy variable_form %} '
                         '<hr style="border:0">'
                     '</div>'
                     '<div id="method">'
                         '{% load crispy_forms_tags %} '
                         '{% crispy method_form %} '
                         '<hr style="border:0">'
                     '</div>'
                 '</div>'
                 '<div class="form-group col-sm-6 col-xs-12">'
                     '<div id="processinglevel">'
                         '{% load crispy_forms_tags %} '
                         '{% crispy processing_level_form %} '
                         '<hr style="border:0">'
                     '</div>'
                     '<div id="timeseriesresult">'
                         '{% load crispy_forms_tags %} '
                         '{% crispy timeseries_result_form %} '
                     '</div>'
                 '</div>')
        )

        # get the context from hs_core
        context = page_processors.get_page_context(page, request.user, resource_edit=edit_resource, extended_metadata_layout=ext_md_layout, request=request)

        # customize base context
        context['resource_type'] = 'Time Series Resource'
        context['site_form'] = site_form
        context['variable_form'] = variable_form
        context['method_form'] = method_form
        context['processing_level_form'] = processing_level_form
        context['timeseries_result_form'] = timeseries_result_form

    # TODO: can we refactor to make it impossible to skip adding the generic context
    hs_core_context = add_generic_context(request, page)
    context.update(hs_core_context)
    return context
