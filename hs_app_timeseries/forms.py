import os

from django.forms import ModelForm
from django import forms

from crispy_forms.layout import Layout, HTML
from crispy_forms.bootstrap import Field

from hs_core.forms import BaseFormHelper
from models import Site, Variable, Method, ProcessingLevel, TimeSeriesResult


class SiteFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('site_code', css_class=field_width),
                        Field('site_name', css_class=field_width),
                        Field('organization', css_class=field_width),
                        Field('elevation_m', css_class=field_width),
                        Field('elevation_datum', css_class=field_width),
                        Field('site_type', css_class=field_width),
                 )

        super(SiteFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                             layout,  *args, **kwargs)


class SiteForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_site_types = list(kwargs['cv_site_types'])
        self.cv_elevation_datums = list(kwargs['cv_elevation_datums'])
        kwargs.pop('cv_site_types')
        kwargs.pop('cv_elevation_datums')
        super(SiteForm, self).__init__(*args, **kwargs)
        self.helper = SiteFormHelper(allow_edit, res_short_id, element_id, element_name='Site')

    def set_dropdown_widgets(self, site_type, elevation_datum):
        cv_site_type_choices = _get_cv_dropdown_widget_items(self.cv_site_types, site_type)
        self.fields['site_type'].widget = forms.Select(choices=cv_site_type_choices)

        cv_e_datum_choices = _get_cv_dropdown_widget_items(self.cv_elevation_datums,
                                                           elevation_datum)
        self.fields['elevation_datum'].widget = forms.Select(choices=cv_e_datum_choices)

    @property
    def form_id(self):
        form_id = 'id_site_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_site_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type']
        exclude = ['content_object']
        widgets = {'elevation_m': forms.TextInput()}


class SiteValidationForm(forms.Form):
    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255)
    elevation_m = forms.IntegerField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)


class VariableFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('variable_code', css_class=field_width),
                     Field('variable_name', css_class=field_width),
                     Field('variable_type', css_class=field_width),
                     Field('no_data_value', css_class=field_width),
                     Field('variable_definition', css_class=field_width),
                     Field('speciation', css_class=field_width),
                )

        super(VariableFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                 element_name, layout,  *args, **kwargs)


class VariableForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_variable_types = list(kwargs['cv_variable_types'])
        self.cv_variable_names = list(kwargs['cv_variable_names'])
        self.cv_speciations = list(kwargs['cv_speciations'])
        kwargs.pop('cv_variable_types')
        kwargs.pop('cv_variable_names')
        kwargs.pop('cv_speciations')
        super(VariableForm, self).__init__(*args, **kwargs)
        self.helper = VariableFormHelper(allow_edit, res_short_id, element_id,
                                         element_name='Variable')

    def set_dropdown_widgets(self, variable_type, variable_name, speciation):
        cv_var_type_choices = _get_cv_dropdown_widget_items(self.cv_variable_types, variable_type)
        self.fields['variable_type'].widget = forms.Select(choices=cv_var_type_choices)

        cv_var_name_choices = _get_cv_dropdown_widget_items(self.cv_variable_names, variable_name)
        self.fields['variable_name'].widget = forms.Select(choices=cv_var_name_choices)

        cv_speciation_choices = _get_cv_dropdown_widget_items(self.cv_speciations, speciation)
        self.fields['speciation'].widget = forms.Select(choices=cv_speciation_choices)

    @property
    def form_id(self):
        form_id = 'id_variable_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_variable_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Variable
        fields = ['variable_code', 'variable_name', 'variable_type', 'no_data_value',
                  'variable_definition', 'speciation']
        exclude = ['content_object']
        widgets = {'no_data_value': forms.TextInput()}


class VariableValidationForm(forms.Form):
    variable_code = forms.CharField(max_length=20)
    variable_name = forms.CharField(max_length=100)
    variable_type = forms.CharField(max_length=100)
    no_data_value = forms.IntegerField()
    variable_definition = forms.CharField(max_length=255, required=False)
    speciation = forms.CharField(max_length=255, required=False)


class MethodFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                         Field('method_code', css_class=field_width),
                         Field('method_name', css_class=field_width),
                         Field('method_type', css_class=field_width),
                         Field('method_description', css_class=field_width),
                         Field('method_link', css_class=field_width),
                         )

        super(MethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                               layout,  *args, **kwargs)


class MethodForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_method_types = list(kwargs['cv_method_types'])
        kwargs.pop('cv_method_types')
        super(MethodForm, self).__init__(*args, **kwargs)
        self.helper = MethodFormHelper(allow_edit, res_short_id, element_id, element_name='Method')

    def set_dropdown_widgets(self, current_method_type):
        cv_method_type_choices = _get_cv_dropdown_widget_items(self.cv_method_types,
                                                               current_method_type)
        self.fields['method_type'].widget = forms.Select(choices=cv_method_type_choices)

    @property
    def form_id(self):
        form_id = 'id_method_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_method_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Method
        fields = ['method_code', 'method_name', 'method_type', 'method_description', 'method_link']
        exclude = ['content_object']
        widgets = {'method_code': forms.TextInput()}


class MethodValidationForm(forms.Form):
    method_code = forms.CharField(max_length=50)
    method_name = forms.CharField(max_length=200)
    method_type = forms.CharField(max_length=200)
    method_description = forms.CharField(required=False)
    method_link = forms.URLField(required=False)


class ProcessingLevelFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('processing_level_code', css_class=field_width),
                     Field('definition', css_class=field_width),
                     Field('explanation', css_class=field_width),
                     )
        kwargs['element_name_label'] = 'Processing Level'
        super(ProcessingLevelFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout, *args, **kwargs)


class ProcessingLevelForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ProcessingLevelForm, self).__init__(*args, **kwargs)
        self.helper = ProcessingLevelFormHelper(allow_edit, res_short_id, element_id,
                                                element_name='ProcessingLevel')

    @property
    def form_id(self):
        form_id = 'id_processinglevel_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_processinglevel_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = ProcessingLevel
        fields = ['processing_level_code', 'definition', 'explanation']
        exclude = ['content_object']
        widgets = {'processing_level_code': forms.TextInput()}


class ProcessingLevelValidationForm(forms.Form):
    processing_level_code = forms.IntegerField()
    definition = forms.CharField(max_length=200, required=False)
    explanation = forms.CharField(required=False)


class TimeSeriesResultFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('units_type', css_class=field_width),
                     Field('units_name', css_class=field_width),
                     Field('units_abbreviation', css_class=field_width),
                     Field('status', css_class=field_width),
                     Field('sample_medium', css_class=field_width),
                     Field('value_count', css_class=field_width),
                     Field('aggregation_statistics', css_class=field_width),
                     )
        kwargs['element_name_label'] = 'Time Series Result'
        super(TimeSeriesResultFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout, *args, **kwargs)


class TimeSeriesResultForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_sample_mediums = list(kwargs['cv_sample_mediums'])
        self.cv_units_types = list(kwargs['cv_units_types'])
        self.cv_aggregation_statistics = list(kwargs['cv_aggregation_statistics'])
        self.cv_statuses = list(kwargs['cv_statuses'])
        kwargs.pop('cv_sample_mediums')
        kwargs.pop('cv_units_types')
        kwargs.pop('cv_aggregation_statistics')
        kwargs.pop('cv_statuses')

        super(TimeSeriesResultForm, self).__init__(*args, **kwargs)
        self.helper = TimeSeriesResultFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='TimeSeriesResult')

    def set_dropdown_widgets(self, current_sample_medium, current_units_type,
                             current_agg_statistics, current_status):
        cv_sample_medium_choices = _get_cv_dropdown_widget_items(self.cv_sample_mediums,
                                                                 current_sample_medium)
        self.fields['sample_medium'].widget = forms.Select(choices=cv_sample_medium_choices)
        cv_units_type_choices = _get_cv_dropdown_widget_items(self.cv_units_types,
                                                              current_units_type)
        self.fields['units_type'].widget = forms.Select(choices=cv_units_type_choices)
        cv_status_choices = _get_cv_dropdown_widget_items(self.cv_statuses, current_status)
        self.fields['status'].widget = forms.Select(choices=cv_status_choices)
        cv_agg_statistics_choices = _get_cv_dropdown_widget_items(self.cv_aggregation_statistics,
                                                                  current_agg_statistics)
        self.fields['aggregation_statistics'].widget = forms.Select(
            choices=cv_agg_statistics_choices)

    @property
    def form_id(self):
        form_id = 'id_timeseriesresult_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_timeseriesresult_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = TimeSeriesResult
        fields = ['units_type', 'units_name', 'units_abbreviation', 'status', 'sample_medium',
                  'value_count', 'aggregation_statistics']
        widgets = {'value_count': forms.TextInput()}


class TimeSeriesResultValidationForm(forms.Form):
    units_type = forms.CharField(max_length=255)
    units_name = forms.CharField(max_length=255)
    units_abbreviation = forms.CharField(max_length=20)
    status = forms.CharField(max_length=255)
    sample_medium = forms.CharField(max_length=255)
    value_count = forms.IntegerField()
    aggregation_statistics = forms.CharField(max_length=255)


def _get_cv_dropdown_widget_items(dropdown_items, selected_item_name):
    for item in dropdown_items:
        if item.name == selected_item_name:
            dropdown_items.remove(item)

    cv_items = [(item.name, item.name) for item in dropdown_items]
    cv_items = [(selected_item_name, selected_item_name)] + cv_items
    cv_item_choices = tuple(cv_items)
    return cv_item_choices


def _get_html_snippet(html_snippet_file_name):
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    html_file = os.path.join(cur_dir, 'layout_snippets', html_snippet_file_name)
    with open(html_file, 'r') as fobj:
        html_snippet = fobj.read()
    return html_snippet

UpdateSQLiteLayout = Layout(HTML(_get_html_snippet('update_sqlite_file.html')))
SeriesSelectionLayout = Layout(HTML(_get_html_snippet('series_selection.html')))
TimeSeriesMetaDataLayout = HTML(_get_html_snippet('timeseries_metadata_edit.html'))
