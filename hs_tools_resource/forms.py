__author__ = 'Drew, Jeff & Shaun'
from django.forms import ModelForm, BaseFormSet
from django import forms
from django.forms.models import formset_factory
from models import *
from hs_core.forms import BaseFormHelper
from crispy_forms.helper import FormHelper
from hs_core.hydroshare.utils import get_resource_types
from crispy_forms import *
from crispy_forms.layout import *
from crispy_forms.bootstrap import *

# #TODO: reference hs_core.forms
class UrlBaseFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                        Field('resShortID', type="hidden"),
                 )
        kwargs['element_name_label'] = 'App URL'

        super(UrlBaseFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class UrlBaseForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(UrlBaseForm, self).__init__(*args, **kwargs)
        self.helper = UrlBaseFormHelper(allow_edit, res_short_id, element_id, element_name='RequestUrlBase')


    class Meta:
        model = RequestUrlBase
        fields = ['value','resShortID']
        exclude = ['content_object']


class UrlBaseValidationForm(forms.Form):
    value = forms.CharField(max_length="500")

# The following 3 classes need to have the "field" same as the fields defined in "ToolResourceType" table in models.py
# class ResTypeFormHelper(BaseFormHelper):
#     def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):
#
#         # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
#         field_width = 'form-control input-sm'
#         layout = Layout(
#                         Field('tool_res_type', css_class=field_width),
#                         HTML(
#                             '<ul>'
#                             '{% for r in res_types %}'
#                             '<li>{{ r }}</li>'
#                             '{% endfor %}'
#                             '</ul>'
#                         )
#                  )
#
#         super(ResTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)
#
#
# class ResTypeForm(ModelForm):
#     def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
#         super(ResTypeForm, self).__init__(*args, **kwargs)
#         self.helper = ResTypeFormHelper(allow_edit, res_short_id, element_id, element_name='ToolResourceType')
#
#
#     class Meta:
#         model = ToolResourceType
#         fields = ['tool_res_type']
#         exclude = ['content_object']
#
#
# class ResTypeValidationForm(forms.Form):
#     tool_res_type = forms.Field()
#
#
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
    value = forms.CharField(max_length="500")

parameters_choices = (
                        ('GenericResource', 'GenericResource'),
                        ('RasterResource', 'RasterResource'),
                        ('RefTimeSeries', 'RefTimeSeries'),
                        ('TimeSeriesResource', 'TimeSeriesResource'),
                        ('NetcdfResource', 'NetcdfResource'),
                        ('ModelProgramResource', 'ModelProgramResource'),
                        ('ModelInstanceResource', 'ModelInstanceResource'),
                        ('SWATModelInstanceResource', 'SWATModelInstanceResource'),
                      )

class MetadataField(layout.Field):
          def __init__(self, *args, **kwargs):
              kwargs['css_class'] = 'form-control input-sm'
              super(MetadataField, self).__init__(*args, **kwargs)



class SupportedResTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        layout = Layout(
                        MetadataField('supported_res_types'),
                 )
        kwargs['element_name_label'] = 'Supported Resource Types'
        super(SupportedResTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SupportedResTypesForm(ModelForm):
    supported_res_types = forms.MultipleChoiceField(choices=parameters_choices,
                                                 widget=forms.CheckboxSelectMultiple(
                                                     attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SupportedResTypesForm, self).__init__(*args, **kwargs)
        self.helper = SupportedResTypeFormHelper(allow_edit, res_short_id, element_id, element_name='SupportedResTypes')
        if self.instance:
            try:
                supported_res_types = self.instance.supported_res_types.all()
                if len(supported_res_types) > 0:
                    checked_item_list=[]
                    for parameter in supported_res_types:
                        checked_item_list.append(parameter.description)

                    self.fields['supported_res_types'].initial = checked_item_list
                else:
                    self.fields['supported_res_types'].initial = []

            except TypeError:
                self.fields['supported_res_types'].initial = []
            except AttributeError:
                self.fields['supported_res_types'].initial = []
            except ValueError:
                self.fields['supported_res_types'].initial = []
            except Exception as e:
                self.fields['supported_res_types'].initial = []

    class Meta:
        model = SupportedResTypes


class SupportedResTypesValidationForm(forms.Form):
    supported_res_types = forms.MultipleChoiceField(choices=parameters_choices,required=False)



