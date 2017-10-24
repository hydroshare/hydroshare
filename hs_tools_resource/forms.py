from django.forms import ModelForm
from django import forms

from crispy_forms.layout import Layout, Field, HTML

from models import RequestUrlBase, ToolVersion, SupportedResTypes, SupportedFileTypes, ToolIcon,\
    SupportedSharingStatus, AppHomePageUrl, URLTemplateFileType
from hs_core.forms import BaseFormHelper
from utils import get_SupportedResTypes_choices, get_SupportedFileTypes_choices


# TODO: reference hs_core.forms
class UrlBaseFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = \
            "Resource-level App-launching URL Pattern <a href='/terms#AppURLPattern' target='_blank'>" \
            "<font size='3'>Help</font></a>"

        super(UrlBaseFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class UrlBaseForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(UrlBaseForm, self).__init__(*args, **kwargs)
        self.helper = UrlBaseFormHelper(allow_edit,
                                        res_short_id,
                                        element_id,
                                        element_name='RequestUrlBase')
        self.fields['value'].label = ''

    class Meta:
        model = RequestUrlBase
        fields = ['value']
        exclude = ['content_object']


class UrlValidationForm(forms.Form):
    value = forms.URLField(max_length=1024, required=False)


class AppHomePageUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "App Home Page URL"

        super(AppHomePageUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class AppHomePageUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(AppHomePageUrlForm, self).__init__(*args, **kwargs)
        self.helper = AppHomePageUrlFormHelper(allow_edit,
                                               res_short_id,
                                               element_id,
                                               element_name='AppHomePageUrl')
        self.fields['value'].label = ''

    class Meta:
        model = AppHomePageUrl
        fields = ['value']
        exclude = ['content_object']


class VersionFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are
        # listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                Field('value', css_class=field_width),
        )
        kwargs['element_name_label'] = 'Version'
        super(VersionFormHelper, self).__init__(allow_edit,
                                                res_short_id,
                                                element_id,
                                                element_name,
                                                layout,
                                                *args,
                                                **kwargs)


class VersionForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(VersionForm, self).__init__(*args, **kwargs)
        self.helper = VersionFormHelper(allow_edit,
                                        res_short_id,
                                        element_id,
                                        element_name='ToolVersion')
        self.fields['value'].label = ""

    class Meta:
        model = ToolVersion
        fields = ['value']
        exclude = ['content_object']


class VersionValidationForm(forms.Form):
    value = forms.CharField(max_length=128)


class ToolIconFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None, *args, **kwargs):
        # the order in which the model fields are listed for the
        # FieldSet is the order these fields will be displayed
        data_url = ""
        if "instance" in kwargs:
            webapp_obj = kwargs.pop("instance")
            if webapp_obj and webapp_obj.metadata.tool_icon:
                data_url = webapp_obj.metadata.tool_icon.data_url
        field_width = 'form-control input-sm'
        layout = Layout(
                    Field('value', css_class=field_width),
                    HTML("""
                        <span id="icon-preview-label" class="control-label">Preview</span>
                        <br>
                        <img id="tool-icon-preview" src="{data_url}">
                        """.format(data_url=data_url)),
        )
        kwargs['element_name_label'] = 'Icon URL'
        super(ToolIconFormHelper, self).__init__(allow_edit,
                                                 res_short_id,
                                                 element_id,
                                                 element_name,
                                                 layout,
                                                 *args,
                                                 **kwargs)


class ToolIconForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ToolIconForm, self).__init__(*args, **kwargs)
        self.helper = ToolIconFormHelper(allow_edit,
                                         res_short_id,
                                         element_id,
                                         element_name='ToolIcon',
                                         **kwargs)
        self.fields['value'].label = ""

    class Meta:
        model = ToolIcon
        fields = ['value']
        exclude = ['content_object']


class ToolIconValidationForm(forms.Form):
    value = forms.CharField(max_length=1024, required=False)
    data_url = forms.URLField(required=False)


class MetadataField(Field):
    def __init__(self, *args, **kwargs):
        kwargs['css_class'] = 'form-control input-sm'
        super(MetadataField, self).__init__(*args, **kwargs)


class SupportedResTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True,
                 res_short_id=None,
                 element_id=None,
                 element_name=None,
                 *args, **kwargs):

        # the order in which the model fields are listed for
        # the FieldSet is the order these fields will be displayed
        layout = Layout(MetadataField('supported_res_types'))
        kwargs['element_name_label'] = 'Supported Resource Types'
        super(SupportedResTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout,  *args, **kwargs)


class SupportedResTypesForm(ModelForm):
    supported_res_types = forms.\
        MultipleChoiceField(choices=get_SupportedResTypes_choices(),
                            widget=forms.CheckboxSelectMultiple(
                                    attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        model_instance = kwargs.get('instance')
        super(SupportedResTypesForm, self).__init__(*args, **kwargs)
        self.fields['supported_res_types'].label = "Choose Resource Types:"
        self.helper = SupportedResTypeFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='SupportedResTypes')

        if model_instance:
            supported_res_types = model_instance.supported_res_types.all()
            if len(supported_res_types) > 0:
                # NOTE: The following code works for SWAT res type but does not work here!!!
                # self.fields['supported_res_types'].initial =
                #   [parameter.description for parameter in supported_res_types]

                self.initial['supported_res_types'] = \
                    [parameter.description for parameter in supported_res_types]
            else:
                self.initial['supported_res_types'] = []

    class Meta:
        model = SupportedResTypes
        fields = ('supported_res_types',)


class SupportedResTypesValidationForm(forms.Form):
    supported_res_types = forms.MultipleChoiceField(choices=get_SupportedResTypes_choices(),
                                                    required=False)


class SupportedFileTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True,
                 res_short_id=None,
                 element_id=None,
                 element_name=None,
                 *args, **kwargs):

        # the order in which the model fields are listed for
        # the FieldSet is the order these fields will be displayed
        layout = Layout(MetadataField('supported_file_types'))
        kwargs['element_name_label'] = 'Supported File Types (Composite Resource)'
        super(SupportedFileTypeFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                          element_name, layout,  *args, **kwargs)


class SupportedFileTypesForm(ModelForm):
    supported_file_types = forms.\
        MultipleChoiceField(choices=get_SupportedFileTypes_choices(),
                            widget=forms.CheckboxSelectMultiple(
                                    attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        model_instance = kwargs.get('instance')
        super(SupportedFileTypesForm, self).__init__(*args, **kwargs)
        self.fields['supported_file_types'].label = "Choose File Types:"
        self.helper = SupportedFileTypeFormHelper(allow_edit, res_short_id, element_id,
                                                  element_name='SupportedFileTypes')

        if model_instance:
            supported_file_types = model_instance.supported_file_types.all()
            if len(supported_file_types) > 0:
                # NOTE: The following code works for SWAT res type but does not work here!!!
                # self.fields['supported_res_types'].initial =
                #   [parameter.description for parameter in supported_res_types]

                self.initial['supported_file_types'] = \
                    [parameter.description for parameter in supported_file_types]
            else:
                self.initial['supported_file_types'] = []

    class Meta:
        model = SupportedFileTypes
        fields = ('supported_file_types',)


class SupportedFileTypesValidationForm(forms.Form):
    supported_file_types = forms.MultipleChoiceField(choices=get_SupportedFileTypes_choices(),
                                                     required=False)


class URLTemplateFileTypeFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = \
            "FileType-level App-launching URL Pattern <a href='/terms#AppURLPattern' target='_blank'>" \
            "<font size='3'>Help</font></a>"

        super(URLTemplateFileTypeFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class URLTemplateFileTypeForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(URLTemplateFileTypeForm, self).__init__(*args, **kwargs)
        self.helper = URLTemplateFileTypeFormHelper(allow_edit,
                                                    res_short_id,
                                                    element_id,
                                                    element_name='urltemplatefiletype')
        self.fields['value'].label = ''

    class Meta:
        model = URLTemplateFileType
        fields = ['value']
        exclude = ['content_object']


SupportedSharingStatus_choices = (
    ('Published', 'Published'),
    ('Public', 'Public'),
    ('Discoverable', 'Discoverable'),
    ('Private', 'Private'),
)


class SupportedSharingStatusFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for
        # the FieldSet is the order these fields will be displayed
        layout = Layout(MetadataField('sharing_status'))
        kwargs['element_name_label'] = 'Supported Resource Sharing Status'
        super(SupportedSharingStatusFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id,
                     element_name, layout,  *args, **kwargs)


class SupportedSharingStatusForm(ModelForm):
    sharing_status = forms.MultipleChoiceField(choices=SupportedSharingStatus_choices,
                                               widget=forms.CheckboxSelectMultiple(
                                                attrs={'style': 'width:auto;margin-top:-5px'}))

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        model_instance = kwargs.get('instance')
        super(SupportedSharingStatusForm, self).__init__(*args, **kwargs)
        self.fields['sharing_status'].label = "Choose Sharing Status:"
        self.helper = SupportedSharingStatusFormHelper(allow_edit, res_short_id, element_id,
                                                       element_name='SupportedSharingStatus')
        if model_instance:
            supported_sharing_status = model_instance.sharing_status.all()
            if len(supported_sharing_status) > 0:
                self.initial['sharing_status'] = \
                    [parameter.description for parameter in supported_sharing_status]
            else:
                self.initial['sharing_status'] = []

    class Meta:
        model = SupportedSharingStatus
        fields = ('sharing_status',)


class SupportedSharingStatusValidationForm(forms.Form):
    sharing_status = forms.MultipleChoiceField(choices=SupportedSharingStatus_choices,
                                               required=False)
