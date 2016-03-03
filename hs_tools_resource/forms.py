from django.forms import ModelForm, BaseFormSet
from django import forms

from crispy_forms.layout import Layout, Field

from models import RequestUrlBase, ToolVersion, SupportedResTypes, ToolIcon
from hs_core.forms import BaseFormHelper


# TODO: reference hs_core.forms
class UrlBaseFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = 'App URL'

        super(UrlBaseFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class UrlBaseForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(UrlBaseForm, self).__init__(*args, **kwargs)
        self.helper = UrlBaseFormHelper(allow_edit, res_short_id, element_id, element_name='RequestUrlBase')

    class Meta:
        model = RequestUrlBase
        fields = ['value']
        exclude = ['content_object']


class UrlBaseValidationForm(forms.Form):
    value = forms.URLField(max_length=1024)

# The following 3 classes need to have the "field" same as the fields defined in "ToolResourceType" table in models.py

class VersionFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                Field('value', css_class=field_width),
        )
        kwargs['element_name_label'] = 'Version'
        super(VersionFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class VersionForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        self.helper = VersionFormHelper(allow_edit, res_short_id, element_id, element_name='ToolVersion')

    class Meta:
        model = ToolVersion
        fields = ['value']
        exclude = ['content_object']


class VersionValidationForm(forms.Form):
    value = forms.CharField(max_length=128)


class ToolIconFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                Field('url', css_class=field_width)
        )
        kwargs['element_name_label'] = 'Tool Icon'
        super(ToolIconFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ToolIconForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ToolIconForm, self).__init__(*args, **kwargs)
        self.helper = ToolIconFormHelper(allow_edit, res_short_id, element_id, element_name='ToolIcon')
        self.fields['url'].label = "URL"

    class Meta:
        model = ToolIcon
        fields = ['url']
        exclude = ['content_object']


class ToolIconValidationForm(forms.Form):
    url = forms.CharField(max_length=1024)

parameters_choices = (
    ('GenericResource', 'Generic Resource'),
    ('RasterResource', 'Raster Resource'),
    ('RefTimeSeriesResource', 'HIS Referenced Time Series Resource'),
    ('TimeSeriesResource', 'Time Series Resource'),
    ('NetcdfResource', 'NetCDF Resource'),
    ('ModelProgramResource', 'Model Program Resource'),
    ('ModelInstanceResource', 'Model Instance Resource'),
    ('SWATModelInstanceResource', 'SWAT Model Instance Resource'),
    ('GeographicFeatureResource', 'Geographic Feature Resource'),
    ('ScriptResource', 'Script Resource')
)


class MetadataField(Field):
    def __init__(self, *args, **kwargs):
        kwargs['css_class'] = 'form-control input-sm'
        super(MetadataField, self).__init__(*args, **kwargs)


class SupportedResTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(MetadataField('supported_res_types'))
        kwargs['element_name_label'] = 'Supported Resource Types'
        super(SupportedResTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout,  *args, **kwargs)


class SupportedResTypesForm(ModelForm):
    supported_res_types = forms.MultipleChoiceField(choices=parameters_choices,
                                                    widget=forms.CheckboxSelectMultiple(
                                                            attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SupportedResTypesForm, self).__init__(*args, **kwargs)
        self.fields['supported_res_types'].label = "Choices: "
        self.helper = SupportedResTypeFormHelper(allow_edit, res_short_id, element_id, element_name='SupportedResTypes')
        if self.instance:
            try:
                supported_res_types = self.instance.supported_res_types.all()
                if len(supported_res_types) > 0:
                    checked_item_list = []
                    for parameter in supported_res_types:
                        checked_item_list.append(parameter.description)

                    self.fields['supported_res_types'].initial = checked_item_list
                else:
                    self.fields['supported_res_types'].initial = []
            except:
                self.fields['supported_res_types'].initial = []

    class Meta:
        model = SupportedResTypes
        fields = '__all__'


class SupportedResTypesValidationForm(forms.Form):
    supported_res_types = forms.MultipleChoiceField(choices=parameters_choices, required=False)

