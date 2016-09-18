import json

from django.forms import ModelForm
from django import forms
from django.forms.models import model_to_dict

from crispy_forms.layout import Layout, HTML
from crispy_forms.bootstrap import Field

from hs_core.forms import BaseFormHelper
from models import Site, Variable, Method, ProcessingLevel, TimeSeriesResult, UTCOffSet


NO_SELECTION_DROPDOWN_OPTION = "-----"


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
                            Field('latitude', css_class=field_width),
                            Field('longitude', css_class=field_width),
                     )
        layout = _set_form_helper_layout(common_layout=common_layout, element_name="site",
                                         is_show_element_code_selection=show_site_code_selection,
                                         field_css=field_width)

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
        _set_available_elements_form_field(form=self, elements=available_sites,
                                           element_name="site")
        code_selection_label = "Select any existing sites to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="site_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_sites,
                                               element_code_att_name="site_code",
                                               element_name_att_name="site_name")

    def set_dropdown_widgets(self, site_type=None, elevation_datum=None):
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
                  'site_code_choices', 'latitude', 'longitude']
        exclude = ['content_object']
        widgets = {'elevation_m': forms.TextInput(), 'latitude': forms.TextInput(),
                   'longitude': forms.TextInput()}
        labels = {'latitude': 'WGS84 Latitude*',
                  'longitude': 'WGS84 Longitude*'}


class SiteValidationForm(forms.Form):
    site_code = forms.CharField(max_length=200)
    site_name = forms.CharField(max_length=255)
    elevation_m = forms.IntegerField(required=False)
    elevation_datum = forms.CharField(max_length=50, required=False)
    site_type = forms.CharField(max_length=100, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)
    latitude = forms.FloatField()
    longitude = forms.FloatField()

    def clean_latitude(self):
        lat = self.cleaned_data['latitude']
        if lat < -90 or lat > 90:
            raise forms.ValidationError("Value for latitude must be in the range of -90 to 90")
        return lat

    def clean_longitude(self):
        lon = self.cleaned_data['longitude']
        if lon < -180 or lon > 180:
            raise forms.ValidationError("Value for longitude must be in the range of -180 to 180")
        return lon

    def clean_elevation_datum(self):
        e_datum = self.cleaned_data['elevation_datum']
        if e_datum == NO_SELECTION_DROPDOWN_OPTION:
            e_datum = ''
        return e_datum

    def clean_site_type(self):
        s_type = self.cleaned_data['site_type']
        if s_type == NO_SELECTION_DROPDOWN_OPTION:
            s_type = ''
        return s_type

    def clean(self):
        cleaned_data = super(SiteValidationForm, self).clean()
        elevation_m = cleaned_data.get('elevation_m', None)
        elevation_datum = cleaned_data.get('elevation_datum', '')
        if elevation_m is not None:
            if len(elevation_datum.strip()) == 0:
                self._errors['elevation_datum'] = ["A value for elevation datum is missing"]

        return self.cleaned_data


class VariableFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_variable_code_selection=False, *args, **kwargs):
        field_width = 'form-control input-sm'
        common_layout = Layout(
                     Field('selected_series_id', css_class=field_width, type="hidden"),
                     Field('available_variables', css_class=field_width, type="hidden"),
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

        layout = _set_form_helper_layout(
            common_layout=common_layout, element_name="variable",
            is_show_element_code_selection=show_variable_code_selection,
            field_css=field_width)

        super(VariableFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                 element_name, layout,  *args, **kwargs)


class VariableForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)
    variable_code_choices = forms.ChoiceField(choices=(), required=False)
    available_variables = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_variable_types = list(kwargs.pop('cv_variable_types'))
        self.cv_variable_names = list(kwargs.pop('cv_variable_names'))
        self.cv_speciations = list(kwargs.pop('cv_speciations'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_variables = kwargs.pop('available_variables', [])
        show_variable_code_selection = kwargs.pop('show_variable_code_selection', False)
        super(VariableForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_variable_code_selection = len(available_variables) > 0 and show_variable_code_selection
        self.helper = VariableFormHelper(allow_edit, res_short_id, element_id,
                                         element_name='Variable',
                                         show_variable_code_selection=show_variable_code_selection)
        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(form=self, elements=available_variables,
                                           element_name="variable")
        code_selection_label = "Select any existing variables to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="variable_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_variables,
                                               element_code_att_name="variable_code",
                                               element_name_att_name="variable_name")

    def set_dropdown_widgets(self, variable_type=None, variable_name=None, speciation=None):
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
                  'variable_definition', 'speciation', 'variable_code_choices']
        exclude = ['content_object']
        widgets = {'no_data_value': forms.TextInput()}


class VariableValidationForm(forms.Form):
    variable_code = forms.CharField(max_length=20)
    variable_name = forms.CharField(max_length=100)
    variable_type = forms.CharField(max_length=100)
    no_data_value = forms.IntegerField()
    variable_definition = forms.CharField(max_length=255, required=False)
    speciation = forms.CharField(max_length=255, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean_speciation(self):
        spe = self.cleaned_data['speciation']
        if spe == NO_SELECTION_DROPDOWN_OPTION:
            spe = ''
        return spe

    def clean(self):
        cleaned_data = super(VariableValidationForm, self).clean()
        variable_name = cleaned_data.get('variable_name', None)
        variable_type = cleaned_data.get('variable_type', None)
        if variable_name is None or variable_name == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['variable_name'] = ["A value for variable name is missing"]

        if variable_type is None or variable_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['variable_type'] = ["A value for variable type is missing"]

        return self.cleaned_data


class MethodFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_method_code_selection=False, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        common_layout = Layout(
                         Field('selected_series_id', css_class=field_width, type="hidden"),
                         Field('available_methods', css_class=field_width, type="hidden"),
                         Field('method_code', css_class=field_width),
                         Field('method_name', css_class=field_width),
                         Field('method_type', css_class=field_width,
                               title="Select 'Other...' to specify a new method type term"),
                         Field('method_description', css_class=field_width),
                         Field('method_link', css_class=field_width),
                         )

        layout = _set_form_helper_layout(common_layout=common_layout, element_name="method",
                                         is_show_element_code_selection=show_method_code_selection,
                                         field_css=field_width)

        super(MethodFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name,
                                               layout,  *args, **kwargs)


class MethodForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)
    method_code_choices = forms.ChoiceField(choices=(), required=False)
    available_methods = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        self.cv_method_types = list(kwargs.pop('cv_method_types'))
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_methods = kwargs.pop('available_methods', [])
        show_method_code_selection = kwargs.pop('show_method_code_selection', False)
        super(MethodForm, self).__init__(*args, **kwargs)
        self.selected_series_id = selected_series_id
        show_method_code_selection = len(available_methods) > 0 and show_method_code_selection
        self.helper = MethodFormHelper(allow_edit, res_short_id, element_id, element_name='Method',
                                       show_method_code_selection=show_method_code_selection)

        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(self, available_methods, "method")
        code_selection_label = "Select any existing methods to use for this series"
        _set_element_code_selection_form_field(form=self, form_field_name="method_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id, elements=available_methods,
                                               element_code_att_name="method_code",
                                               element_name_att_name="method_name")

    def set_dropdown_widgets(self, current_method_type=None):
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
        fields = ['method_code', 'method_name', 'method_type', 'method_description',
                  'method_link', 'method_code_choices']
        exclude = ['content_object']
        widgets = {'method_code': forms.TextInput()}


class MethodValidationForm(forms.Form):
    method_code = forms.CharField(max_length=50)
    method_name = forms.CharField(max_length=200)
    method_type = forms.CharField(max_length=200)
    method_description = forms.CharField(required=False)
    method_link = forms.URLField(required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned_data = super(MethodValidationForm, self).clean()
        method_type = cleaned_data.get('method_type', None)
        if method_type is None or method_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['method_type'] = ["A value for method type is missing"]

        return self.cleaned_data


class ProcessingLevelFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 show_processing_level_code_selection=False, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        common_layout = Layout(
                     Field('selected_series_id', css_class=field_width, type="hidden"),
                     Field('available_processinglevels', css_class=field_width, type="hidden"),
                     Field('processing_level_code', css_class=field_width),
                     Field('definition', css_class=field_width),
                     Field('explanation', css_class=field_width),
                     )

        layout = _set_form_helper_layout(
            common_layout=common_layout,
            element_name="processinglevel",
            is_show_element_code_selection=show_processing_level_code_selection,
            field_css=field_width)

        kwargs['element_name_label'] = 'Processing Level'
        super(ProcessingLevelFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout, *args, **kwargs)


class ProcessingLevelForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)
    processinglevel_code_choices = forms.ChoiceField(choices=(), required=False)
    available_processinglevels = forms.CharField(max_length=1000, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        available_processinglevels = kwargs.pop('available_processinglevels', [])
        show_processing_level_code_selection = kwargs.pop('show_processing_level_code_selection',
                                                          False)
        super(ProcessingLevelForm, self).__init__(*args, **kwargs)
        self.helper = ProcessingLevelFormHelper(
            allow_edit, res_short_id, element_id,
            element_name='ProcessingLevel',
            show_processing_level_code_selection=show_processing_level_code_selection)

        self.fields['selected_series_id'].initial = selected_series_id
        _set_available_elements_form_field(self, available_processinglevels, "processinglevel")
        code_selection_label = "Select any existing processing level to use for this series"
        _set_element_code_selection_form_field(form=self,
                                               form_field_name="processinglevel_code_choices",
                                               form_field_label=code_selection_label,
                                               element_id=element_id,
                                               elements=available_processinglevels,
                                               element_code_att_name="processing_level_code",
                                               element_name_att_name="definition")

    @property
    def form_id(self):
        form_id = 'id_processinglevel_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        return "'" + self.form_id + "'"

    class Meta:
        model = ProcessingLevel
        fields = ['processing_level_code', 'definition', 'explanation',
                  'processinglevel_code_choices']
        exclude = ['content_object']
        widgets = {'processing_level_code': forms.TextInput()}


class ProcessingLevelValidationForm(forms.Form):
    processing_level_code = forms.IntegerField()
    definition = forms.CharField(max_length=200, required=False)
    explanation = forms.CharField(required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)


class TimeSeriesResultFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('selected_series_id', css_class=field_width, type="hidden"),
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
                     Field('series_label', css_class=field_width, type="hidden"),
                     )
        kwargs['element_name_label'] = 'Time Series Result'
        super(TimeSeriesResultFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout, *args, **kwargs)


class TimeSeriesResultForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        self.cv_sample_mediums = list(kwargs.pop('cv_sample_mediums'))
        self.cv_units_types = list(kwargs.pop('cv_units_types'))
        self.cv_aggregation_statistics = list(kwargs.pop('cv_aggregation_statistics'))
        self.cv_statuses = list(kwargs.pop('cv_statuses'))

        super(TimeSeriesResultForm, self).__init__(*args, **kwargs)
        self.helper = TimeSeriesResultFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='TimeSeriesResult')
        self.fields['selected_series_id'].initial = selected_series_id

    def set_dropdown_widgets(self, current_sample_medium=None, current_units_type=None,
                             current_agg_statistics=None, current_status=None):
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

    def set_series_label(self, series_label):
        self.fields['series_label'].initial = series_label

    def set_value_count(self, value_count=None):
        if value_count is not None:
            self.fields['value_count'].initial = value_count

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
                  'value_count', 'aggregation_statistics', 'series_label']
        widgets = {'value_count': forms.TextInput()}
        labels = {'aggregation_statistics': 'Aggregation statistic'}


class TimeSeriesResultValidationForm(forms.Form):
    units_type = forms.CharField(max_length=255)
    units_name = forms.CharField(max_length=255)
    units_abbreviation = forms.CharField(max_length=20)
    status = forms.CharField(max_length=255)
    sample_medium = forms.CharField(max_length=255)
    value_count = forms.IntegerField()
    aggregation_statistics = forms.CharField(max_length=255)
    series_label = forms.CharField(max_length=255, required=False)
    selected_series_id = forms.CharField(max_length=50, required=False)

    def clean(self):
        cleaned_data = super(TimeSeriesResultValidationForm, self).clean()
        units_type = cleaned_data.get('units_type', None)
        status = cleaned_data.get('status', None)
        sample_medium = cleaned_data.get('sample_medium', None)
        aggregation_statistics = cleaned_data.get('aggregation_statistics', None)

        if units_type is None or units_type == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['units_type'] = ["A value for units type is missing"]

        if status is None or status == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['status'] = ["A value for status is missing"]

        if sample_medium is None or sample_medium == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['sample_medium'] = ["A value for sample medium is missing"]

        if aggregation_statistics is None or aggregation_statistics == NO_SELECTION_DROPDOWN_OPTION:
            self._errors['aggregation_statistics'] = ["A value for aggregation statistic "
                                                      "is missing"]


class UTCOffSetFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('selected_series_id', css_class=field_width, type="hidden"),
            Field('value', css_class=field_width),
        )
        kwargs['element_name_label'] = 'UTC Offset'
        super(UTCOffSetFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                  element_name, layout, *args, **kwargs)


class UTCOffSetForm(ModelForm):
    selected_series_id = forms.CharField(max_length=50, required=False)

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        selected_series_id = kwargs.pop('selected_series_id', None)
        super(UTCOffSetForm, self).__init__(*args, **kwargs)
        self.helper = UTCOffSetFormHelper(allow_edit, res_short_id, element_id,
                                          element_name='UTCOffSet')
        self.fields['selected_series_id'].initial = selected_series_id
        if not element_id:
            self.fields['value'].initial = ""

    class Meta:
        model = UTCOffSet
        fields = ['value']
        exclude = ['content_object']
        widgets = {'value': forms.TextInput()}
        labels = {'value': ""}


class UTCOffSetValidationForm(forms.Form):
    value = forms.FloatField(required=True)


def _get_cv_dropdown_widget_items(dropdown_items, selected_item_name):
    # filter out the item that needs to shown as the currently selected item
    # in the dropdown list
    dropdown_items = [item for item in dropdown_items if item.name != selected_item_name]

    # sort the cv items
    cv_item_names = [item.name for item in dropdown_items]
    cv_item_names.sort(key=unicode.lower)

    # create a list of tuples from item names
    cv_items = [(item_name, item_name) for item_name in cv_item_names]

    if selected_item_name is None or len(selected_item_name) == 0:
        selected_item_name = NO_SELECTION_DROPDOWN_OPTION
        cv_items = [(selected_item_name, selected_item_name)] + cv_items
    else:
        cv_items = [(selected_item_name, selected_item_name)] + cv_items + \
                   [(NO_SELECTION_DROPDOWN_OPTION, NO_SELECTION_DROPDOWN_OPTION)]

    cv_item_choices = tuple(cv_items)
    return cv_item_choices


def _set_available_elements_form_field(form, elements, element_name):
    elements_data = []
    for element in elements:
        element_data = model_to_dict(element, exclude=["object_id", "series_ids", "content_type"])
        elements_data.append(element_data)
    element_data_str = ""
    if len(elements_data) > 0:
        element_data_str = json.dumps(elements_data)
    form_field_name = "available_{}s".format(element_name)
    form.fields[form_field_name].initial = element_data_str


def _set_element_code_selection_form_field(form, form_field_name, form_field_label, element_id,
                                           elements, element_code_att_name, element_name_att_name):
    element_display_str = "{code_att_name}:{name_att_name}"
    if len(elements) > 0:
        if len(form.initial) > 0:
            element_code_choices = [(getattr(element, element_code_att_name),
                                     element_display_str.format(
                                         code_att_name=str(getattr(element, element_code_att_name)),
                                         name_att_name=getattr(element, element_name_att_name))
                                     ) for element in elements if element.id != element_id]

            element_code_choices = tuple([(form.initial[element_code_att_name],
                                          element_display_str.format(
                                            code_att_name=str(form.initial[element_code_att_name]),
                                            name_att_name=form.initial[element_name_att_name]))] +
                                         element_code_choices + [("----", "----")])

        else:
            element_code_choices = [(getattr(element, element_code_att_name),
                                     element_display_str.format(
                                         code_att_name=str(getattr(element, element_code_att_name)),
                                         name_att_name=getattr(element, element_name_att_name)))
                                    for element in elements]

            element_code_choices = tuple([("----", "----")] + element_code_choices)

        form.fields[form_field_name].widget = forms.Select(
            choices=element_code_choices)
        form.fields[form_field_name].label = form_field_label


def _set_form_helper_layout(common_layout, element_name, is_show_element_code_selection, field_css):
    form_field_name = "{}_code_choices".format(element_name)
    if is_show_element_code_selection:
        element_choice_help = "Select '----' for a new {} or any other option to use an " \
                        "existing {} for this series".format(element_name, element_name)

        layout = Layout(
            Field(form_field_name, css_class=field_css, title=element_choice_help),
            common_layout,
        )
    else:
        layout = Layout(
            Field(form_field_name, css_class=field_css, type="hidden"),
            common_layout,
        )
    return layout

UpdateSQLiteLayout = Layout(HTML("""
<div id="sql-file-update" class="row"
{% if not cm.can_update_sqlite_file or not cm.metadata.is_dirty %}style="display:none;
  "{% endif %} style="margin-bottom:10px">
    <div class="col-sm-12">
        <div class="alert alert-warning alert-dismissible" role="alert">
            <strong>SQLite file needs to be synced with metadata changes.</strong>
            {% if cm.metadata.series_names %}
                <div>
                <strong><span style="color:red;">NOTE:</span> New resource specific metadata
                elements can't be created after you update the SQLite file.</strong>
                </div>
            {% endif %}
            <input id="can-update-sqlite-file" type="hidden"
            value="{{ cm.can_update_sqlite_file }}">
            <input id="metadata-dirty" type="hidden" value="{{ cm.metadata.is_dirty }}">
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
        <strong>Select a timeseries to see corresponding metadata (Number of
            timeseries: {{ series_ids.items|length }}):</strong>
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
UTCOffSetLayout = HTML("""
<div class="form-group col-sm-6 col-xs-12 time-series-forms">
     <div id="utc_offset">
         {% load crispy_forms_tags %}
         {% crispy utcoffset_form %}
         <hr style="border:0">
     </div>
</div>
""")

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
