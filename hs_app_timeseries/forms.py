import json

from django.forms import ModelForm
from django import forms
from django.forms.models import model_to_dict

from crispy_forms.layout import Layout, HTML
from crispy_forms.bootstrap import Field

from hs_core.forms import BaseFormHelper
from models import Site, Variable, Method, ProcessingLevel, TimeSeriesResult


class SiteFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_site_code_selection=False, *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        common_layout = Layout(
                            Field('selected_series_id', css_class=field_width, type="hidden"),
                            Field('available_sites', css_class=field_width, type="hidden"),
                            Field('site_code', css_class=field_width),
                            Field('site_name', css_class=field_width),
                            Field('organization', css_class=field_width),
                            Field('elevation_m', css_class=field_width),
                            Field('elevation_datum', css_class=field_width,
                                  title="Select 'Other...' to specify a new elevation datum term"),
                            Field('site_type', css_class=field_width,
                                  title="Select 'Other...' to specify a new site type term"),
                     )
        if show_site_code_selection:
            layout = Layout(
                            Field('site_code_choices', css_class=field_width),
                            common_layout,
                     )
        else:
            layout = Layout(
                Field('site_code_choices', css_class=field_width, type="hidden"),
                common_layout,
            )
        super(SiteFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                             layout,  *args, **kwargs)


class SiteForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)
    site_code_choices = forms.ChoiceField(choices=(), required=False)
    available_sites = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_site_types = list(kwargs.pop('cv_site_types'))
        self.cv_elevation_datums = list(kwargs.pop('cv_elevation_datums'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_sites = kwargs.pop('available_sites', [])
        show_site_code_selection = kwargs.pop('show_site_code_selection', False)
        super(SiteForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_site_code_selection = len(available_sites) > 0 and show_site_code_selection
        self.helper = SiteFormHelper(allow_edit, res_short_id, element_id, element_name='Site',
                                     show_site_code_selection=show_site_code_selection)
        self.fields['selected_series_id'].initial = selected_series_id
        sites_data = []
        for site in available_sites:
            site_data = model_to_dict(site, exclude=["object_id", "series_ids", "content_type"])
            sites_data.append(site_data)
        sites_data_str = ""
        if len(sites_data) > 0:
            sites_data_str = json.dumps(sites_data)
        self.fields['available_sites'].initial = sites_data_str
        if len(available_sites) > 0:
            if self.instance:
                site_code_choices = [(s.site_code, s.site_code) for s in available_sites
                                     if s.id != self.instance.id]
                site_code_choices = tuple([(self.instance.site_code, self.instance.site_code)] +
                                          site_code_choices + [("----", "----")])
            else:
                site_code_choices = [(s.site_code, s.site_code) for s in available_sites]
                site_code_choices = tuple([("----", "----")] + site_code_choices)
            self.fields['site_code_choices'].widget = forms.Select(choices=site_code_choices)
            self.fields['site_code_choices'].label = "Select a site code to use an existing site"

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
        return "'" + self.form_id + "'"

    class Meta:
        model = Site
        fields = ['site_code', 'site_name', 'elevation_m', 'elevation_datum', 'site_type',
                  'site_code_choices'
                  ]
        exclude = ['content_object']
        widgets = {'elevation_m': forms.TextInput()}


class SiteValidationForm(forms.Form):
    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255)
    elevation_m = forms.IntegerField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)


class VariableFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_multiple_variable_chkbox=False, *args, **kwargs):
        field_width = 'form-control input-sm'
        common_layout = Layout(
                     Field('selected_series_id', css_class=field_width, type="hidden"),
                     Field('variable_code', css_class=field_width),
                     Field('variable_name', css_class=field_width,
                           title="Select 'Other...' to specify a new variable name term"),
                     Field('variable_type', css_class=field_width,
                           title="Select 'Other...' to specify a new variable type term"),
                     Field('no_data_value', css_class=field_width),
                     Field('variable_definition', css_class=field_width),
                     Field('speciation', css_class=field_width,
                           title="Select 'Other...' to specify a new speciation term"),
                )

        if show_multiple_variable_chkbox:
            layout = Layout(
                Field('multiple_variables', css_class=field_width),
                common_layout,
            )
        else:
            layout = Layout(
                Field('multiple_variables', css_class=field_width, type="hidden"),
                common_layout,
            )
        super(VariableFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                 element_name, layout,  *args, **kwargs)


class VariableForm(ModelForm):
    multiple_variables = forms.BooleanField(required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_variable_types = list(kwargs.pop('cv_variable_types'))
        self.cv_variable_names = list(kwargs.pop('cv_variable_names'))
        self.cv_speciations = list(kwargs.pop('cv_speciations'))
        show_multiple_variable_chkbox = kwargs.pop('show_multiple_variable_chkbox')
        selected_series_id = kwargs.pop('selected_series_id', None)
        super(VariableForm, self).__init__(*args, **kwargs)
        self.helper = VariableFormHelper(allow_edit, res_short_id, element_id,
                                         element_name='Variable',
                                         show_multiple_variable_chkbox=
                                         show_multiple_variable_chkbox)
        self.fields['selected_series_id'].initial = selected_series_id

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
        return "'" + self.form_id + "'"

    class Meta:
        model = Variable
        fields = ['variable_code', 'variable_name', 'variable_type', 'no_data_value',
                  'variable_definition', 'speciation', 'multiple_variables']
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
                         Field('method_type', css_class=field_width,
                               title="Select 'Other...' to specify a new method type term"),
                         Field('method_description', css_class=field_width),
                         Field('method_link', css_class=field_width),
                         )

        super(MethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                               layout,  *args, **kwargs)


class MethodForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_method_types = list(kwargs.pop('cv_method_types'))
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
        return "'" + self.form_id + "'"

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
        return "'" + self.form_id + "'"

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
                     Field('units_type', css_class=field_width,
                           title="Select 'Other...' to specify a new units type term"),
                     Field('units_name', css_class=field_width),
                     Field('units_abbreviation', css_class=field_width),
                     Field('status', css_class=field_width,
                           title="Select 'Other...' to specify a new status term"),
                     Field('sample_medium', css_class=field_width,
                           title="Select 'Other...' to specify a new sample medium term"),
                     Field('value_count', css_class=field_width),
                     Field('aggregation_statistics', css_class=field_width,
                           title="Select 'Other...' to specify a new aggregation statistics term"),
                     )
        kwargs['element_name_label'] = 'Time Series Result'
        super(TimeSeriesResultFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout, *args, **kwargs)


class TimeSeriesResultForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_sample_mediums = list(kwargs.pop('cv_sample_mediums'))
        self.cv_units_types = list(kwargs.pop('cv_units_types'))
        self.cv_aggregation_statistics = list(kwargs.pop('cv_aggregation_statistics'))
        self.cv_statuses = list(kwargs.pop('cv_statuses'))

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
        return "'" + self.form_id + "'"

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
    # filter out the item that needs to shown as the currently selected item
    # in the dropdown list
    dropdown_items = [item for item in dropdown_items if item.name != selected_item_name]

    # create a list of tuples
    cv_items = [(item.name, item.name) for item in dropdown_items]

    # add the selected item as a tuple to the beginning of the list of items
    # so that it will be displayed as the currently selected item
    cv_items = [(selected_item_name, selected_item_name)] + cv_items
    cv_item_choices = tuple(cv_items)
    return cv_item_choices

UpdateSQLiteLayout = Layout(HTML("""
<div id="sql-file-update" class="row"
{% if not cm.has_sqlite_file or not cm.metadata.is_dirty  %}style="display:none;
  "{% endif %} style="margin-bottom:10px">
    <div class="col-sm-12">
        <div class="alert alert-warning alert-dismissible" role="alert">
        <strong>SQLite file needs to be synced with metadata changes:</strong>
        <input id="has-sqlite-file" type="hidden" value="{{ cm.has_sqlite_file }}">
        <form action="/timeseries/sqlite/update/{{ cm.short_id }}/" method="post"
        enctype="multipart/form-data">
            {% csrf_token %}
            <input name="resource-mode" type="hidden" value="edit">
            <button type="button" class="btn btn-primary" onclick="this.form.submit();
            return false;">Update SQLite File</button>
        </form>
            </div>
    </div>
</div>
"""
                                 )
                            )

SeriesSelectionLayout = Layout(HTML("""
<div id="div-series-selection">
    <div class="col-sm-12">
        <strong>Select a timeseries to see corresponding metadata(Number of
            timeseries:{{ series_ids.items|length }}):</strong>
        <form action="/resource/{{ cm.short_id }}/" method="get" enctype="multipart/form-data">
            {% csrf_token %}
            <input name="resource-mode" type="hidden" value="edit">
            <select class="form-control" name="series_id" id="series_id"
            onchange="this.form.submit()">
                {% for series_id, label in series_ids.items %}
                    {% if selected_series_id == series_id %}
                        <option value="{{ series_id }}" selected="selected"
                                title="{{ label }}">{{ label|slice:":120"|add:"..." }}</option>
                    {% else %}
                        <option value="{{ series_id }}" title="{{ label }}">
                        {{ label|slice:":120"|add:"..." }}</option>
                    {% endif %}
                {% endfor %}
            </select>
        </form>
        <hr>
    </div>
</div>
"""
                                    )
                               )

TimeSeriesMetaDataLayout = HTML("""
<div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="site">
         {% load crispy_forms_tags %}
         {% crispy site_form %}
         <hr style="border:0">
     </div>
     <div id="variable">
         {% load crispy_forms_tags %}
         {% crispy variable_form %}
         <hr style="border:0">
     </div>
     <div id="method">
         {% load crispy_forms_tags %}
         {% crispy method_form %}
         <hr style="border:0">
     </div>
 </div>

 <div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="processinglevel">
         {% load crispy_forms_tags %}
         {% crispy processing_level_form %}
         <hr style="border:0">
     </div>
     <div id="timeseriesresult">
         {% load crispy_forms_tags %}
         {% crispy timeseries_result_form %}
     </div>
 </div>
"""
                                )
