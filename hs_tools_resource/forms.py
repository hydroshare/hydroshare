from django.forms import ModelForm
from django import forms

from crispy_forms.layout import Layout, Field, HTML

from models import RequestUrlBase, AppHomePageUrl, TestingProtocolUrl, \
    HelpPageUrl, SourceCodeUrl, IssuesPageUrl, MailingListUrl, Roadmap, \
    ShowOnOpenWithList, ToolVersion, ToolIcon, SupportedResTypes, SupportedSharingStatus

from hs_core.forms import BaseFormHelper
from utils import get_SupportedResTypes_choices, get_SupportedSharingStatus_choices


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
            "App-launching URL Pattern <a href='/terms#AppURLPattern' target='_blank'>" \
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


class TestingProtocolUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Testing Protocol URL"

        super(TestingProtocolUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class TestingProtocolUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(TestingProtocolUrlForm, self).__init__(*args, **kwargs)
        self.helper = TestingProtocolUrlFormHelper(allow_edit,
                                                   res_short_id,
                                                   element_id,
                                                   element_name='TestingProtocolUrl')
        self.fields['value'].label = ''

    class Meta:
        model = TestingProtocolUrl
        fields = ['value']
        exclude = ['content_object']


class HelpPageUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Help Page URL"

        super(HelpPageUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class HelpPageUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(HelpPageUrlForm, self).__init__(*args, **kwargs)
        self.helper = HelpPageUrlFormHelper(allow_edit,
                                            res_short_id,
                                            element_id,
                                            element_name='HelpPageUrl')
        self.fields['value'].label = ''

    class Meta:
        model = HelpPageUrl
        fields = ['value']
        exclude = ['content_object']


class SourceCodeUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Source Code URL"

        super(SourceCodeUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SourceCodeUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SourceCodeUrlForm, self).__init__(*args, **kwargs)
        self.helper = SourceCodeUrlFormHelper(allow_edit,
                                              res_short_id,
                                              element_id,
                                              element_name='SourceCodeUrl')
        self.fields['value'].label = ''

    class Meta:
        model = SourceCodeUrl
        fields = ['value']
        exclude = ['contednt_object']


class IssuesPageUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Issues Page URL"

        super(IssuesPageUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class IssuesPageUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(IssuesPageUrlForm, self).__init__(*args, **kwargs)
        self.helper = IssuesPageUrlFormHelper(allow_edit,
                                              res_short_id,
                                              element_id,
                                              element_name='IssuesPageUrl')
        self.fields['value'].label = ''

    class Meta:
        model = IssuesPageUrl
        fields = ['value']
        exclude = ['content_object']


class MailingListUrlFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Mailing List URL"

        super(MailingListUrlFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class MailingListUrlForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(MailingListUrlForm, self).__init__(*args, **kwargs)
        self.helper = MailingListUrlFormHelper(allow_edit,
                                               res_short_id,
                                               element_id,
                                               element_name='MailingListUrl')
        self.fields['value'].label = ''

    class Meta:
        model = MailingListUrl
        fields = ['value']
        exclude = ['content_object']


class RoadmapFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Roadmap"

        super(RoadmapFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class RoadmapForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(RoadmapForm, self).__init__(*args, **kwargs)
        self.helper = RoadmapFormHelper(allow_edit,
                                        res_short_id,
                                        element_id,
                                        element_name='Roadmap')
        self.fields['value'].label = ''

    class Meta:
        model = Roadmap
        fields = ['value']
        exclude = ['content_object']


class ShowOnOpenWithListFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None,
                 element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed
        # for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
            Field('value', css_class=field_width)
        )
        kwargs['element_name_label'] = "Show on 'Open With' List"

        super(ShowOnOpenWithListFormHelper, self).\
            __init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ShowOnOpenWithListForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ShowOnOpenWithListForm, self).__init__(*args, **kwargs)
        self.helper = ShowOnOpenWithListFormHelper(allow_edit,
                                                   res_short_id,
                                                   element_id,
                                                   element_name='ShowOnOpenWithList')
        self.fields['value'].label = ''

    class Meta:
        model = ShowOnOpenWithList
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
            if webapp_obj and webapp_obj.metadata.app_icon:
                data_url = webapp_obj.metadata.app_icon.data_url
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
    sharing_status = forms.MultipleChoiceField(choices=get_SupportedSharingStatus_choices(),
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
    sharing_status = forms.MultipleChoiceField(choices=get_SupportedSharingStatus_choices(),
                                               required=False)
