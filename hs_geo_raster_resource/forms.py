from django.forms import ModelForm, BaseFormSet
from django import forms
from crispy_forms.layout import *
from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper
from django.forms.models import formset_factory

class OriginalCoverageSpatialFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('Place/Area Name', css_class=field_width),
                        Field('Coordinate System/Geographic Projection', css_class=field_width),
                        Field('Coordinate Units', css_class=field_width),
                        Field('North Longitude', css_class=field_width),
                        Field('East Latitude', css_class=field_width),
                        Field('South Longitude', css_class=field_width),
                        Field('West Latitude', css_class=field_width),
                 )

        super(OriginalCoverageSpatialFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class OriginalCoverageSpatialForm(forms.Form):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(OriginalCoverageSpatialForm, self).__init__(*args, **kwargs)
        self.helper = OriginalCoverageSpatialFormHelper(allow_edit, res_short_id, element_id, element_name='OriginalCoverage')

        # only noDataValue field needs to be set up read-only or not depending on whether the value is extracted from file or not
        if not allow_edit:
            self.fields['name'].widget.attrs['readonly'] = "readonly"
            self.fields['projection'].widget.attrs['readonly'] = "readonly"
            self.fields['units'].widget.attrs['readonly'] = "readonly"

    class Meta:
        model = OriginalCoverage
        fields = ['name', 'projection', 'units', 'northLimit', 'eastLimit', 'southLimit', 'westLimit']
        exclude = ['content_object']
        widgets = { 'name': forms.TextInput(),
                    'projection': forms.TextInput(),
                    'units': forms.TextInput(),
                    'northLimit': forms.TextInput(attrs={'readonly':'readonly'}),
                    'eastLimit': forms.TextInput(attrs={'readonly':'readonly'}),
                    'southLimit': forms.TextInput(attrs={'readonly':'readonly'}),
                    'westLimit': forms.TextInput(attrs={'readonly':'readonly'})}

class OriginalCoverageSpatialValidationForm(forms.Form):
    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    projection = forms.CharField(max_length=100, required=False, label='Coordinate System/Geographic Projection')
    units = forms.CharField(max_length=50, label='Coordinate Units')
    northLimit = forms.DecimalField(label='North Longitude', widget=forms.TextInput())
    eastLimit = forms.DecimalField(label='East Latitude', widget=forms.TextInput())
    southLimit = forms.DecimalField(label='South Longitude', widget=forms.TextInput())
    westLimit = forms.DecimalField(label='West Latitude', widget=forms.TextInput())

class CellInfoFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('rows', css_class=field_width),
                        Field('columns', css_class=field_width),
                        Field('cellSizeXValue', css_class=field_width),
                        Field('cellSizeYValue', css_class=field_width),
                        Field('cellSizeUnit', css_class=field_width),
                        Field('cellDataType', css_class=field_width),
                        Field('noDataValue', css_class=field_width),
                 )

        super(CellInfoFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class CellInfoForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CellInfoForm, self).__init__(*args, **kwargs)
        self.helper = CellInfoFormHelper(allow_edit, res_short_id, element_id, element_name='CellInformation')

        # only noDataValue field needs to be set up read-only or not depending on whether the value is extracted from file or not
        if not allow_edit:
            self.fields['noDataValue'].widget.attrs['readonly'] = "readonly"

    class Meta:
        model = CellInformation
        fields = ['rows', 'columns', 'cellSizeXValue', 'cellSizeYValue', 'cellSizeUnit', 'cellDataType', 'noDataValue']
        exclude = ['content_object']
        widgets = { 'rows': forms.TextInput(attrs={'readonly':'readonly'}),
                    'columns': forms.TextInput(attrs={'readonly':'readonly'}),
                    'cellSizeXValue': forms.TextInput(attrs={'readonly':'readonly'}),
                    'cellSizeYValue': forms.TextInput(attrs={'readonly':'readonly'}),
                    'cellSizeUnit': forms.TextInput(attrs={'readonly':'readonly'}),
                    'cellDataType': forms.TextInput(attrs={'readonly':'readonly'}),
                    'noDataValue': forms.TextInput()}

class CellInfoValidationForm(forms.Form):
    rows = forms.IntegerField(required=True)
    columns = forms.IntegerField(required=True)
    cellSizeXValue = forms.FloatField(required = True)
    cellSizeYValue = forms.FloatField(required = True)
    cellSizeUnit = forms.CharField(max_length=50, required = True)
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

        super(BandInfoFormHelper, self).__init__(res_short_id, element_id, element_name, layout,  *args, **kwargs)

class BandInfoForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(BandInfoForm, self).__init__(*args, **kwargs)
        self.helper = BandInfoFormHelper(res_short_id, element_id, element_name='BandInformation')
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
    comment = forms.CharField(required=False)

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
                             '{% for form in bandinfo_formset.forms %} '
                                 '<div class="item form-group"> '
                                 '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                 '{% crispy form %} '
                                 '<div class="row" style="margin-top:10px">'
                                    '<div class="col-md-12">'
                                        '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save Changes</button>'
                                    '</div>'
                                 '</div>'
                                 '</form> '
                                 '</div> '
                             '{% endfor %}'
                        ),
                    )