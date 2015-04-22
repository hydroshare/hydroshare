__author__ = 'Shaun'
from django.forms import ModelForm, BaseFormSet
from django import forms
from django.forms.models import formset_factory
from crispy_forms.layout import *
from crispy_forms.bootstrap import *
from models import *
from hs_core.forms import BaseFormHelper
from crispy_forms.helper import FormHelper
from hs_core.hydroshare.utils import get_resource_types

#TODO: reference hs_core.forms
class UrlBaseFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                 )

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
    value = forms.CharField(max_length="500")

# The following 3 classes need to have the "field" same as the fields defined in "ToolResourceType" table in models.py
class ResTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('tool_res_type', css_class=field_width),
                        HTML(
                            '<h4>available resource types</h4>'
                            '{% for r in res_types %}'
                            '<p>{{ r.content_object.model }}</p>'
                            '{% endfor %}'
                        )
                 )

        super(ResTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ResTypeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ResTypeForm, self).__init__(*args, **kwargs)
        self.helper = ResTypeFormHelper(allow_edit, res_short_id, element_id, element_name='ToolResourceType')


    class Meta:
        model = ToolResourceType
        fields = ['tool_res_type']
        exclude = ['content_object']


class ResTypeValidationForm(forms.Form):
    tool_res_type = forms.Field()


class FeeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        field_width = 'form-control input-sm'
        # change the fields name here
        layout = Layout(
                     Field('description', css_class=field_width),
                     Field('value', css_class=field_width),
                )

        super(FeeFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class FeeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(FeeForm, self).__init__(*args, **kwargs)
        self.helper = FeeFormHelper(allow_edit, res_short_id, element_id, element_name='Fee')
        self.delete_modal_form = None
        self.number = 0
        self.allow_edit = allow_edit
        if res_short_id:
            self.action = "/hsapi/_internal/%s/fee/add-metadata/" % res_short_id
        else:
            self.action = ""

    @property
    def form_id(self):
        form_id = 'id_fee_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_fee_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Fee
        fields = ['description', 'value']
        exclude = ['content_object']


class FeeValidationForm(forms.Form):
    description = forms.CharField(min_length="0")
    value = forms.DecimalField(max_digits=10, decimal_places=2)


# class BaseFeeFormSet(BaseFormSet):
#     def add_fields(self, form, index):
#         super(BaseFeeFormSet, self).add_fields(form, index)


    # def get_metadata_dict(self):
    #     fees_data = []
    #     for form in self.forms:
    #         fee_data = {k: v for k, v in form.cleaned_data.iteritems()}
    #
    #         fees_data.append({'Fee': fee_data})
    #
    #     return fees_data

#FeeFormSet = formset_factory(FeeForm, formset=BaseFeeFormSet, extra=0)


ModalDialogLayoutAddFee = Layout(
                            HTML('<div class="modal fade" id="add-fee-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                    '<div class="modal-dialog">'
                                        '<div class="modal-content">'
                                            '<form action="{{ add_fee_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
                                            '{% csrf_token %} '
                                            '<input name="resource-mode" type="hidden" value="edit"/>'
                                            '<div class="modal-header">'
                                                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                '<h4 class="modal-title" id="myModalLabel">Add Fee</h4>'
                                            '</div>'
                                            '<div class="modal-body">'
                                                '{% csrf_token %}'
                                                '<div class="form-group">'
                                                    '{% load crispy_forms_tags %} '
                                                    '{% crispy add_fee_modal_form %} '
                                                '</div>'
                                            '</div>'
                                            '<div class="modal-footer">'
                                                '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'
                                                '<button type="submit" class="btn btn-primary">Save changes</button>'
                                            '</div>'
                                            '</form>'
                                        '</div>'
                                    '</div>'
                                '</div>'
                            )
                        )

FeeLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in fee_formset.forms %} '
                                     '<div class="item form-group"> '
                                     '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                     '{% crispy form %} '
                                    '<div class="row" style="margin-top:10px">'
                                        '<div class="col-md-10">'
                                            '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-fee-element-dialog_{{ form.number }}" value="Delete Fee">'
                                        '</div>' #change
                                        '<div class="col-md-2">'
                                            '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save Changes</button>'  # change
                                        '</div>'
                                    '</div>'
                                    '{% crispy form.delete_modal_form %} '
                                    '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-fee" class="btn btn-success" data-toggle="modal" data-target="#add-fee-dialog">'
                                 '<i class="fa fa-plus"></i>Add another Fee</a>'
                                 '</div>'
                            ),
                    )


class VersionFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                     Field('value', css_class=field_width),
                     )
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






