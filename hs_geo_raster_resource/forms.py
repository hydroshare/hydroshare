from django.forms import ModelForm, BaseFormSet
from django import forms
from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper
from django.forms.models import formset_factory
import copy


class OriginalCoverageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('projection', css_class=field_width),
                        Field('units', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width)
                 )

        super(OriginalCoverageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Spatial Reference', *args, **kwargs)


class OriginalCoverageSpatialForm(forms.Form):
    projection = forms.CharField(max_length=100, required=False, label='Coordinate Reference System')
    northlimit = forms.DecimalField(label='North Extent', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Extent', widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    southlimit = forms.DecimalField(label='South Extent', widget=forms.TextInput(attrs={'readonly': 'readonly'}))
    westlimit = forms.DecimalField(label='West Extent', widget=forms.TextInput())
    units = forms.CharField(max_length=50, label='Coordinate Reference System Unit')

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(OriginalCoverageSpatialForm, self).__init__(*args, **kwargs)
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
        super(OriginalCoverageSpatialForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        is_form_errors = False
        for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit', 'units'):
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

        if 'projection' in temp_cleaned_data:
            if len(temp_cleaned_data['projection']) == 0:
                del temp_cleaned_data['projection']

        self.cleaned_data['value'] = copy.deepcopy(temp_cleaned_data)

        if 'northlimit' in self.cleaned_data:
                del self.cleaned_data['northlimit']
        if 'eastlimit' in self.cleaned_data:
                del self.cleaned_data['eastlimit']
        if 'southlimit' in self.cleaned_data:
            del self.cleaned_data['southlimit']
        if 'westlimit' in self.cleaned_data:
            del self.cleaned_data['westlimit']
        if 'units' in self.cleaned_data:
            del self.cleaned_data['units']
        if 'projection' in self.cleaned_data:
            del self.cleaned_data['projection']

        return self.cleaned_data


class CellInfoFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('rows', css_class=field_width),
                        Field('columns', css_class=field_width),
                        Field('cellSizeXValue', css_class=field_width),
                        Field('cellSizeYValue', css_class=field_width),
                        Field('cellDataType', css_class=field_width),
                        Field('noDataValue', css_class=field_width)
                 )

        super(CellInfoFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout, element_name_label='Cell Information', *args, **kwargs)


class CellInfoForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CellInfoForm, self).__init__(*args, **kwargs)
        self.helper = CellInfoFormHelper(allow_edit, res_short_id, element_id, element_name='CellInformation')

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = CellInformation
        fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellDataType', 'noDataValue']
        exclude = ['content_object']
        widgets = { 'rows': forms.TextInput(attrs={'readonly':'readonly'}),
                    'columns': forms.TextInput(attrs={'readonly':'readonly'}),
                    'cellSizeXValue': forms.TextInput(), #(attrs={'readonly':'readonly'}),
                    'cellSizeYValue': forms.TextInput(), #(attrs={'readonly':'readonly'}),
                    'cellDataType': forms.TextInput(attrs={'readonly':'readonly'}),
                    'noDataValue': forms.TextInput()}


class CellInfoValidationForm(forms.Form):
    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required = True)
    cellSizeYValue = forms.FloatField(required = True)
    cellDataType = forms.CharField(max_length=50, required=True)
    noDataValue = forms.FloatField(required = False)


# repeatable element related forms
class BandBaseFormHelper(FormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None, element_layout=None,  *args, **kwargs):
        super(BandBaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            if element_id:
                self.form_tag = True
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % (res_short_id, element_name, element_id)
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
                                     HTML('<div style="margin-top:10px">'
                                          '<button type="submit" class="btn btn-primary">Save changes</button>'
                                          '</div>')
                            )
                         )
        else:
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                            )
                          )


class BandInfoFormHelper(BandBaseFormHelper):
    def __init__(self, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('name', css_class=field_width),
                        Field('variableName', css_class=field_width),
                        Field('variableUnit', css_class=field_width),
                        Field('method', css_class=field_width),
                        Field('comment', css_class=field_width)
                 )

        super(BandInfoFormHelper, self).__init__(res_short_id, element_id, element_name, layout, *args, **kwargs)


class BandInfoForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(BandInfoForm, self).__init__(*args, **kwargs)
        self.helper = BandInfoFormHelper(res_short_id, element_id, element_name='Band Information')
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        if res_short_id:
            self.action = "/hsapi/_internal/%s/bandinformation/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        form_id = 'id_bandinformation_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_bandinformation_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = BandInformation
        fields = ['name', 'variableName', 'variableUnit', 'method', 'comment']
        exclude = ['content_object']
        widgets = {'variableName': forms.TextInput(),
                   'comment': forms.Textarea,
                   'method': forms.Textarea}


class BandInfoValidationForm(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    variableName = forms.CharField(max_length=100, required=True)
    variableUnit = forms.CharField(max_length=50, required=True)
    method = forms.CharField(required=False)
    comment = forms.CharField(required=True)


class BaseBandInfoFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super(BaseBandInfoFormSet, self).add_fields(form, index)

    def get_metadata_dict(self):
        bands_data = []
        for form in self.forms:
            band_data = {k: v for k, v in form.cleaned_data.iteritems()}
            bands_data.append({'BandInformation': band_data})
        return bands_data

BandInfoFormSet = formset_factory(BandInfoForm, formset=BaseBandInfoFormSet, extra=0)

BandInfoLayoutEdit = Layout(
    HTML('{% load crispy_forms_tags %} '
         '<div class="col-sm-12 pull-left">'
             '<div id="variables" class="well">'
                 '<div class="row">'
                     '{% for form in bandinfo_formset.forms %}'
                     '<div class="col-sm-3 col-xs-12">'
                         '<form id="{{form.form_id}}" action="{{ form.action }}" method="POST" enctype="multipart/form-data">'
                             '{% crispy form %}'
                             '<div class="row" style="margin-top:10px">'
                                 '<div class="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6">'
                                     '<button type="button" class="btn btn-primary pull-right" '
                                     'onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;"'
                                     '>Save Changes</button>'
                                 '</div>'
                             '</div>'
                         '</form>'
                     '</div>'
                     '{% endfor %}'
                 '</div>'
             '</div>'
         '</div>'
         )
)
