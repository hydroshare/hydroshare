from django.forms import ModelForm, Textarea, BaseFormSet
from django import forms
from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from django.forms.models import formset_factory
from django.forms.models import modelformset_factory
from hs_geo_raster_resource.models import *
from functools import partial, wraps

# Keep this one unchanged
class BaseFormHelper(FormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, element_layout=None, *args, **kwargs):
        super(BaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            if element_id:
                self.form_tag = True
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % (res_short_id,element_name, element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % (res_short_id, element_name)
                self.form_tag = False
        else:
            self.form_tag = False

        # change the first character to uppercase of the element name
        element_name = element_name.title()
        if res_short_id and element_id:
            self.layout = Layout(
                            Fieldset(element_name,
                            element_layout,
                            HTML('<div style="margin-top:10px">'),
                            HTML('<button type="submit" class="btn btn-primary">Save changes</button>'),
                            HTML('</div>')
                            ),
                        )
        else:
            self.layout = Layout(
                            Fieldset(element_name,
                            element_layout,
                            ),
                        )

class RasterMetadataValidationForm(forms.Form):
    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required = True)
    cellSizeYValue = forms.FloatField(required = True)
    cellSizeUnit = forms.CharField(max_length=50, required = True)
    cellDataType = forms.CharField(max_length=50, required=True)
    cellNoDataValue = forms.FloatField(required = False)
    bandCount =forms.IntegerField(required=True)
    bandName_1 = forms.CharField(max_length=50, required=True)
    variableName_1 = forms.CharField(widget=forms.Textarea, required=True)
    variableUnit_1 = forms.CharField(max_length=50, required=True)
    method_1 = forms.CharField(widget=forms.Textarea, required=False)
    comment_1 = forms.CharField(widget=forms.Textarea, required=False)
