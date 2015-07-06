__author__ = 'drew'

from django import forms
from hs_core.forms import BaseFormHelper
from crispy_forms.layout import Layout, Field
import copy
import json

class OriginalCoverageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('projection_name', css_class=field_width),
                        Field('datum', css_class=field_width),
                        Field('unit', css_class=field_width),
                        Field('projection_string', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width),
                        )

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Spatial Reference', *args, **kwargs)


class OriginalCoverageForm(forms.Form):
    projection_string = forms.CharField(max_length=1024, required=False, label='Coordinate String')
    projection_name = forms.CharField(max_length=1024, required=False, label='Coordinate Reference System')
    datum = forms.CharField(max_length=1024, required=False, label='Datum')
    unit = forms.CharField(max_length=1024, required=False, label='Unit')

    northlimit = forms.FloatField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.FloatField(label='East Extent', widget=forms.TextInput())
    southlimit = forms.FloatField(label='South Extent', widget=forms.TextInput())
    westlimit = forms.FloatField(label='West Extent', widget=forms.TextInput())


    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(OriginalCoverageForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageFormHelper(allow_edit, res_short_id, element_id, element_name='OriginalCoverage')
        self.delete_modal_form = None
        self.number = 0
        self.delete_modal_form = None
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"
        # enabling all element fields for editing
        # else:
        #     self.fields['projection'].widget.attrs['readonly'] = True
        #     self.fields['projection'].widget.attrs['style'] = "background-color:white;"
        #     self.fields['units'].widget.attrs['readonly'] = True
        #     self.fields['units'].widget.attrs['style'] = "background-color:white;"

    def clean(self):
        # modify the form's cleaned_data dictionary
        super(OriginalCoverageForm, self).clean()

        is_form_errors = False
        extent={}
        for bound in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
            if self.cleaned_data.get(bound, None):
                v=self.cleaned_data[bound]
                if isinstance(v, float):
                    extent[bound]=self.cleaned_data[bound]
                else:
                    self._errors[bound] = ["Data for %s is not float" % bound]
                    is_form_errors = True
                    break
            else:
                self._errors[bound] = ["Data for %s is missing" % bound]
                is_form_errors = True
                break

        if not is_form_errors:
           self.cleaned_data["extent"] = extent

        return self.cleaned_data


class OriginalCoverageValidationForm(forms.Form):
    northlimit = forms.FloatField(required=True)
    eastlimit = forms.FloatField(required=True)
    southlimit = forms.FloatField(required=True)
    westlimit = forms.FloatField(required=True)


class FieldInformationFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('fieldName', css_class=field_width),
                        Field('fieldType', css_class=field_width),
                        )

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Spatial Reference', *args, **kwargs)


class FieldInformationForm(forms.Form):
    fieldName = forms.CharField(max_length=50, label='Field Name')
    fieldType = forms.CharField(max_length=50, label='Field Type')
    fieldTypeCode = forms.CharField(max_length=50, label='Field Type Code')
    fieldWidth = forms.DecimalField(label='Field Width', widget=forms.TextInput())
    fieldPrecision = forms.DecimalField(label='Field Precision', widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(FieldInformationForm, self).__init__(*args, **kwargs)
        self.helper = FieldInformationForm(allow_edit, res_short_id, element_id, element_name='FieldInformation')
        self.delete_modal_form = None
        self.number = 0
        self.delete_modal_form = None
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"
        # enabling all element fields for editing
        # else:
        #     self.fields['projection'].widget.attrs['readonly'] = True
        #     self.fields['projection'].widget.attrs['style'] = "background-color:white;"
        #     self.fields['units'].widget.attrs['readonly'] = True
        #     self.fields['units'].widget.attrs['style'] = "background-color:white;"

    def clean(self):
        # modify the form's cleaned_data dictionary
        super(FieldInformationForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False
        for limit in ('fieldName', 'fieldType', 'fieldTypeCode', 'fieldWidth', 'fieldPrecision'):
            limit_data = temp_cleaned_data.get(limit, None)
            if not limit_data:
                self._errors[limit] = ["Data for %s is missing" % limit]
                is_form_errors = True
                del self.cleaned_data[limit]

        if is_form_errors:
            return self.cleaned_data

        temp_cleaned_data['fieldName'] = str(temp_cleaned_data['fieldName'])
        temp_cleaned_data['fieldType'] = str(temp_cleaned_data['fieldType'])
        temp_cleaned_data['fieldTypeCode'] = str(temp_cleaned_data['fieldTypeCode'])
        temp_cleaned_data['fieldWidth'] = str(temp_cleaned_data['fieldWidth'])
        temp_cleaned_data['fieldPrecision'] = str(temp_cleaned_data['fieldPrecision'])

        if 'fieldTypeCode' in temp_cleaned_data:
            if len(temp_cleaned_data['fieldTypeCode']) == 0:
                del temp_cleaned_data['fieldTypeCode']

        if 'fieldPrecision' in temp_cleaned_data:
            if len(temp_cleaned_data['fieldPrecision']) == 0:
                del temp_cleaned_data['fieldPrecision']

        if 'fieldWidth' in temp_cleaned_data:
            if len(temp_cleaned_data['fieldWidth']) == 0:
                del temp_cleaned_data['fieldWidth']

        self.cleaned_data['value'] = copy.deepcopy(temp_cleaned_data)

        if 'fieldName' in self.cleaned_data:
            del self.cleaned_data['fieldName']
        if 'fieldType' in self.cleaned_data:
            del self.cleaned_data['fieldType']



        return self.cleaned_data

class FieldInformationValidationForm(forms.Form):
    fieldName = forms.CharField(required=True, max_length=50)
    fieldType = forms.CharField(required=True, max_length=50)
    fieldTypeCode = forms.CharField(required=False, max_length=50,)
    fieldWidth = forms.DecimalField(required=False)
    fieldPrecision = forms.DecimalField(required=False)


class GeometryInformationFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('geometryType', css_class=field_width),
                        Field('featureCount', css_class=field_width),
                        )

        super(GeometryInformationFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Geometry Information', *args, **kwargs)


class GeometryInformationForm(forms.Form):
    geometryType = forms.CharField(max_length=128, required=True, label='Geometry Type')
    featureCount = forms.IntegerField(label='Feature Count', required=True, widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(GeometryInformationForm, self).__init__(*args, **kwargs)
        self.helper = GeometryInformationFormHelper(allow_edit, res_short_id, element_id, element_name='GeometryInformation')
        self.delete_modal_form = None
        self.number = 0
        self.delete_modal_form = None
        self.allow_edit = allow_edit
        self.errors.clear()

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"
        # enabling all element fields for editing
        # else:
        #     self.fields['projection'].widget.attrs['readonly'] = True
        #     self.fields['projection'].widget.attrs['style'] = "background-color:white;"
        #     self.fields['units'].widget.attrs['readonly'] = True
        #     self.fields['units'].widget.attrs['style'] = "background-color:white;"

    def clean(self):
        # modify the form's cleaned_data dictionary
        super(GeometryInformationForm, self).clean()

        is_form_errors = False
        out={}
        for ele in ('geometryType', 'featureCount'):
            if self.cleaned_data.get(ele, None):
                v=self.cleaned_data[ele]
                out[ele]=self.cleaned_data[ele]
            else:
                self._errors[ele] = ["Data for %s is missing" % ele]
                is_form_errors = True
                break

        if not is_form_errors:
            self.cleaned_data["geometryType"] = out["geometryType"]
            self.cleaned_data["featureCount"] = out["featureCount"]

        return self.cleaned_data


class GeometryInformationValidationForm(forms.Form):
    featureCount = forms.IntegerField(required=True)
    geometryType = forms.CharField(max_length=128, required=True)