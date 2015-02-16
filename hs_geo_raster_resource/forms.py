from django.forms import ModelForm
from django import forms
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper

class CellInfoFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('rows', css_class=field_width),
                        Field('columns', css_class=field_width),
                        Field('cellSizeXValue', css_class=field_width),
                        Field('cellSizeYValue', css_class=field_width),
                        Field('cellSizeUnit', css_class=field_width),
                        Field('cellDataType', css_class=field_width),
                        Field('cellNoDataValue', css_class=field_width),
                 )

        super(CellInfoFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class CellInfoForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(CellInfoForm, self).__init__(*args, **kwargs)
        self.helper = CellInfoFormHelper(allow_edit, res_short_id, element_id, element_name='CellInformation')

    class Meta:
        model = CellInformation
        fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellSizeUnit', 'cellDataType', 'noDataValue']
        exclude = ['content_object']
        widgets = {'CellInformation': forms.TextInput()}

class CellInfoValidationForm(forms.Form):
    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required = True)
    cellSizeYValue = forms.FloatField(required = True)
    cellSizeUnit = forms.CharField(max_length=50, required = True)
    cellDataType = forms.CharField(max_length=50, required=True)
    cellNoDataValue = forms.FloatField(required = False)

class BandInfoFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('name', css_class=field_width),
                        Field('variableName', css_class=field_width),
                        Field('variableUnit', css_class=field_width),
                        Field('method', css_class=field_width),
                        Field('comment', css_class=field_width)
                 )

        super(BandInfoFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class BandInfoForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(BandInfoForm, self).__init__(*args, **kwargs)
        self.helper = BandInfoFormHelper(allow_edit, res_short_id, element_id, element_name='BandInformation')

    class Meta:
        model = BandInformation
        fields = ['name', 'variableName', 'variableUnit', 'method', 'comment']
        exclude = ['content_object']
        widgets = {'variableName': forms.TextInput()}

class BandInfoValidationForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    variableName = forms.CharField(max_length=100, required=True)
    variableUnit = forms.CharField(max_length=50, required=True)
    method = forms.CharField(widget=forms.Textarea, required=False)
    comment = forms.CharField(widget=forms.Textarea, required=False)
