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
        site_form = SiteForm()
        variable_form = VariableForm()
        ext_md_layout = Layout(
                                HTML("<div class='form-group' id='site'>"),
                                HTML('{% load crispy_forms_tags %} {% crispy site_form %}'),
                                HTML("<p></p>"),
                                HTML("<div class='form-group' id='variable'>"),
                                HTML('{% load crispy_forms_tags %} {% crispy variable_form %}'),
                        )


        context = page_processors.get_page_context(page, extended_metadata_layout=ext_md_layout)

        context['site_form'] = site_form
        context['variable_form'] = variable_form
        return context


        # site_form = SiteForm()
        # variable_form = VariableForm()
        # method_form = MethodForm()
        # proc_level_form = ProcessingLevelForm()
        # time_series_res_form = TimeSeriesResultForm()
        # return {'site_form': site_form, 'variable_form': variable_form, 'method_form': method_form,
        #         'proc_level_form': proc_level_form, 'time_series_res_form': time_series_res_form}