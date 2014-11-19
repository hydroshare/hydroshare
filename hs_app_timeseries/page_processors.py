__author__ = 'hydro'
from mezzanine.pages.page_processors import processor_for
from models import TimeSeriesResource
from forms import *


@processor_for(TimeSeriesResource)
def main_page(request, page):
    content_model = page.get_content_model()
    if request.method == 'POST':
        site_form = SiteForm(request.POST)
        variable_form = VariableForm(request.POST)
        method_form = MethodForm(request.POST)
        proc_level_form = ProcessingLevelForm(request.POST)
        time_series_res_form = TimeSeriesResultForm(request.POST)
        if site_form.is_valid() and variable_form.is_valid() and method_form.is_valid() and proc_level_form.is_valid() \
                and time_series_res_form.is_valid():
            # TODO: do we know that we are creating a resource and not updating a resource
            content_model.metadata.create_element('site', site_form.cleaned_data)
            content_model.metadata.create_element('variable', variable_form.cleaned_data)
            content_model.metadata.create_element('method', method_form.cleaned_data)
            content_model.metadata.create_element('processinglevel', proc_level_form.cleaned_data)
            content_model.metadata.create_element('timeseriesresult', time_series_res_form.cleaned_data)
            content_model.save()
    else:
        site_form = SiteForm()
        variable_form = VariableForm()
        method_form = MethodForm()
        proc_level_form = ProcessingLevelForm()
        time_series_res_form = TimeSeriesResultForm()
        return {'site_form': site_form, 'variable_form': variable_form, 'method_form': method_form,
                'proc_level_form': proc_level_form, 'time_series_res_form': time_series_res_form}