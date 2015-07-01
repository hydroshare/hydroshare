__author__ = 'drew'

from django import forms
from hs_core.forms import BaseFormHelper
from crispy_forms.layout import Layout, Field
import copy

class OriginalCoverageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('projection_string', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width),
                        )

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Spatial Reference', *args, **kwargs)


class OriginalCoverageForm(forms.Form):
    projection_string = forms.CharField(max_length=1024, required=False, label='Coordinate Reference System')
    northlimit = forms.DecimalField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Extent', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Extent', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Extent', widget=forms.TextInput())


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
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
            limit_data = temp_cleaned_data.get(limit, None)
            if not limit_data:
                self._errors[limit] = ["Data for %s is missing" % limit]
                is_form_errors = True
                del self.cleaned_data[limit]

        if is_form_errors:
            return self.cleaned_data

        temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
        temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
        temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
        temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])

        if 'projection_string' in temp_cleaned_data:
            if len(temp_cleaned_data['projection_string']) == 0:
                del temp_cleaned_data['projection_string']

        self.cleaned_data['value'] = copy.deepcopy(temp_cleaned_data)

        if 'northlimit' in self.cleaned_data:
            del self.cleaned_data['northlimit']
        if 'eastlimit' in self.cleaned_data:
            del self.cleaned_data['eastlimit']
        if 'southlimit' in self.cleaned_data:
            del self.cleaned_data['southlimit']
        if 'westlimit' in self.cleaned_data:
            del self.cleaned_data['westlimit']


        return self.cleaned_data
