"""Django forms for hs_core module."""

import copy

from django.forms import ModelForm, BaseFormSet
from django.contrib.admin.widgets import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, HTML
from crispy_forms.bootstrap import Field

from hydroshare import utils
from models import Party, Creator, Contributor, validate_user_url, Relation, Source, Identifier, \
    FundingAgency, Description


class Helper(object):
    """Render resusable elements to use in Django forms."""

    @classmethod
    def get_element_add_modal_form(cls, element_name, modal_form_context_name):
        """Apply a modal UI element to a given form.

        Used in netCDF and modflow_modelinstance apps
        """
        modal_title = "Add %s" % element_name.title()
        layout = Layout(
                        HTML('<div class="modal fade" id="add-element-dialog" tabindex="-1" '
                             'role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                             '<div class="modal-dialog">'
                             '<div class="modal-content">'),
                        HTML('<form action="{{ form.action }}" '
                             'method="POST" enctype="multipart/form-data"> '),
                        HTML('{% csrf_token %} '
                             '<input name="resource-mode" type="hidden" value="edit"/>'
                             '<div class="modal-header">'
                             '<button type="button" class="close" '
                             'data-dismiss="modal" aria-hidden="true">&times;'
                             '</button>'),
                        HTML('<h4 class="modal-title" id="myModalLabel"> Add Element </h4>'),
                        HTML('</div>'
                             '<div class="modal-body">'
                             '{% csrf_token %}'
                             '<div class="form-group">'),
                        HTML('{% load crispy_forms_tags %} {% crispy add_creator_modal_form %} '),
                        HTML('</div>'
                             '</div>'
                             '<div class="modal-footer">'
                             '<button type="button" class="btn btn-default" '
                             'data-dismiss="modal">Close</button>'
                             '<button type="submit" class="btn btn-primary">'
                             'Save changes</button>'
                             '</div>'
                             '</form>'
                             '</div>'
                             '</div>'
                             '</div>')
                        )

        layout[0] = HTML('<div class="modal fade" id="add-%s-dialog" tabindex="-1" role="dialog" '
                         'aria-labelledby="myModalLabel" aria-hidden="true">'
                         '<div class="modal-dialog">'
                         '<div class="modal-content">' % element_name.lower())
        layout[1] = HTML('<form action="{{ %s.action }}" method="POST" '
                         'enctype="multipart/form-data"> ' % modal_form_context_name)
        layout[3] = HTML('<h4 class="modal-title" id="myModalLabel"> {title} '
                         '</h4>'.format(title=modal_title),)
        html_str = '{% load crispy_forms_tags %} {% crispy' + ' add_{element}_modal_form'.format(
            element=element_name.lower()) + ' %}'
        layout[5] = HTML(html_str)

        return layout


# the 1st and the 3rd HTML layout objects get replaced in MetaDataElementDeleteForm class
def _get_modal_confirm_delete_matadata_element():
    layout = Layout(
                    HTML('<div class="modal fade" id="delete-metadata-element-dialog" '
                         'tabindex="-1" role="dialog" aria-labelledby="myModalLabel" '
                         'aria-hidden="true">'),
                    HTML('<div class="modal-dialog">'
                         '<div class="modal-content">'
                         '<div class="modal-header">'
                         '<button type="button" class="close" data-dismiss="modal" '
                         'aria-hidden="true">&times;</button>'
                         '<h4 class="modal-title" id="myModalLabel">'
                         'Delete metadata element</h4>'
                         '</div>'
                         '<div class="modal-body">'
                         '<strong>Are you sure you want to delete this metadata '
                         'element?</strong>'

                         '</div>'
                         '<div class="modal-footer">'
                         '<button type="button" class="btn btn-default" '
                         'data-dismiss="modal">Cancel</button>'),
                    HTML('<a type="button" class="btn btn-danger" href="">Delete</a>'),
                    HTML('</div>'
                         '</div>'
                         '</div>'
                         '</div>'),
                    )
    return layout


class MetaDataElementDeleteForm(forms.Form):
    """Render a modal that confirms element deletion."""

    def __init__(self, res_short_id, element_name, element_id, *args, **kwargs):
        """Render a modal that confirms element deletion.

        uses _get_modal_confirm_delete_matadata_element
        """
        super(MetaDataElementDeleteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.delete_element_action = '"/hsapi/_internal/%s/%s/%s/delete-metadata/"' % \
                                     (res_short_id, element_name, element_id)
        self.helper.layout = _get_modal_confirm_delete_matadata_element()
        self.helper.layout[0] = HTML('<div class="modal fade" id="delete-%s-element-dialog_%s" '
                                     'tabindex="-1" role="dialog" aria-labelledby="myModalLabel" '
                                     'aria-hidden="true">' % (element_name, element_id))
        self.helper.layout[2] = HTML('<a type="button" class="btn btn-danger" '
                                     'href=%s>Delete</a>' % self.delete_element_action)
        self.helper.form_tag = False


class ExtendedMetadataForm(forms.Form):
    """Render an extensible metadata form via the extended_metadata_layout kwarg."""

    def __init__(self, resource_mode='edit', extended_metadata_layout=None, *args, **kwargs):
        """Render an extensible metadata form via the extended_metadata_layout kwarg."""
        super(ExtendedMetadataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = extended_metadata_layout


class CreatorFormSetHelper(FormHelper):
    """Render a creator form with custom HTML5 validation and error display."""

    def __init__(self, *args, **kwargs):
        """Render a creator form with custom HTML5 validation and error display."""
        super(CreatorFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order
        # these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = True
        self.layout = Layout(
            Fieldset('Creator',
                     Field('name', css_class=field_width),
                     Field('description', css_class=field_width),
                     Field('organization', css_class=field_width),
                     Field('email', css_class=field_width),
                     Field('address', css_class=field_width),
                     Field('phone', css_class=field_width),
                     Field('homepage', css_class=field_width),
                     Field('order', css_class=field_width),
                     ),
        )


class PartyForm(ModelForm):
    """Render form for creating and editing Party models, aka people."""

    def __init__(self, *args, **kwargs):
        """Render form for creating and editing Party models, aka people.

        Removes profile link formset and renders proper description URL
        """
        if 'initial' in kwargs:
            if 'description' in kwargs['initial']:
                if kwargs['initial']['description']:
                    kwargs['initial']['description'] = utils.current_site_url() + \
                                                       kwargs['initial']['description']
        super(PartyForm, self).__init__(*args, **kwargs)
        self.profile_link_formset = None
        self.number = 0

    class Meta:
        """Describe meta properties of PartyForm.

        Fields that will be displayed are specified here - but not necessarily in the same order
        """

        model = Party
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage']

        # TODO: field labels and widgets types to be specified
        labels = {'description': 'HydroShare User Identifier (URL)'}


class CreatorForm(PartyForm):
    """Render form for creating and editing Creator models, as in creators of resources."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render form for creating and editing Creator models, as in creators of resources."""
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/creator/add-metadata/" % res_short_id
        else:
            self.action = ""
        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

            self.fields['order'].widget.attrs['readonly'] = True
            self.fields['order'].widget.attrs['style'] = "background-color:white;"
        else:
            if 'add-metadata' in self.action:
                del self.fields['order']

    @property
    def form_id(self):
        """Render proper form id by prepending 'id_creator_'."""
        form_id = 'id_creator_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        """Render proper form id with quotes around it."""
        form_id = 'id_creator_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        """Describe meta properties of PartyForm."""

        model = Creator
        fields = PartyForm.Meta.fields
        fields.append("order")
        labels = PartyForm.Meta.labels


class PartyValidationForm(forms.Form):
    """Validate form for Party models."""

    description = forms.CharField(required=False, validators=[validate_user_url])
    name = forms.CharField(required=False, max_length=100)
    organization = forms.CharField(max_length=200, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=250, required=False)
    phone = forms.CharField(max_length=25, required=False)
    homepage = forms.URLField(required=False)
    identifiers = forms.CharField(required=False)

    def clean_description(self):
        """Create absolute URL for Party.description field."""
        user_absolute_url = self.cleaned_data['description']
        if user_absolute_url:
            url_parts = user_absolute_url.split('/')
            if len(url_parts) > 4:
                return '/user/{user_id}/'.format(user_id=url_parts[4])
        return user_absolute_url

    def clean_identifiers(self):
        data = self.cleaned_data['identifiers']
        return Party.validate_identifiers(data)

    def clean(self):
        """Validate that name and/or organization are present in form data."""
        cleaned_data = super(PartyValidationForm, self).clean()
        name = cleaned_data.get('name', None)
        org = cleaned_data.get('organization', None)
        if not org:
            if not name or len(name.strip()) == 0:
                self._errors['name'] = ["A value for name or organization is required but both "
                                        "are missing"]

        return self.cleaned_data


class CreatorValidationForm(PartyValidationForm):
    """Validate form for Creator models. Extends PartyValidationForm."""

    order = forms.IntegerField(required=False)


class ContributorValidationForm(PartyValidationForm):
    """Validate form for Contributor models. Extends PartyValidationForm."""

    pass


class BaseCreatorFormSet(BaseFormSet):
    """Render BaseFormSet for working with Creator models."""

    def add_fields(self, form, index):
        """Pass through add_fields function to super."""
        super(BaseCreatorFormSet, self).add_fields(form, index)

    def get_metadata(self):
        """Collect and append creator data to form fields."""
        creators_data = []
        for form in self.forms:
            creator_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if creator_data:
                creators_data.append({'creator': creator_data})

        return creators_data


class ContributorFormSetHelper(FormHelper):
    """Render layout for Contributor model form and activate required fields."""

    def __init__(self, *args, **kwargs):
        """Render layout for Contributor model form and activate required fields."""
        super(ContributorFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order
        # these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.layout = Layout(
            Fieldset('Contributor',
                     Field('name', css_class=field_width),
                     Field('description', css_class=field_width),
                     Field('organization', css_class=field_width),
                     Field('email', css_class=field_width),
                     Field('address', css_class=field_width),
                     Field('phone', css_class=field_width),
                     Field('homepage', css_class=field_width),
                     ),
        )

        self.render_required_fields = True,


class ContributorForm(PartyForm):
    """Render Contributor model form with appropriate attributes."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render Contributor model form with appropriate attributes."""
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.helper = ContributorFormSetHelper()
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/contributor/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        """Render proper form id by prepending 'id_contributor_'."""
        form_id = 'id_contributor_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        """Render proper form id  with quotes around it."""
        form_id = 'id_contributor_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        """Describe meta properties of ContributorForm, removing 'order' field."""

        model = Contributor
        fields = PartyForm.Meta.fields
        labels = PartyForm.Meta.labels
        if 'order' in fields:
            fields.remove('order')


class BaseContributorFormSet(BaseFormSet):
    """Render BaseFormSet for working with Contributor models."""

    def add_fields(self, form, index):
        """Pass through add_fields function to super."""
        super(BaseContributorFormSet, self).add_fields(form, index)

    def get_metadata(self):
        """Collect and append contributor data to form fields."""
        contributors_data = []
        for form in self.forms:
            contributor_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if contributor_data:
                contributors_data.append({'contributor': contributor_data})

        return contributors_data


class RelationFormSetHelper(FormHelper):
    """Render layout for Relation form including HTML5 valdiation and errors."""

    def __init__(self, *args, **kwargs):
        """Render layout for Relation form including HTML5 valdiation and errors."""
        super(RelationFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order
        # these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = False
        self.layout = Layout(
            Fieldset('Relation',
                     Field('type', css_class=field_width),
                     Field('value', css_class=field_width),
                     ),
        )


class RelationForm(ModelForm):
    """Render Relation model form with appropriate attributes."""

    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
        """Render Relation model form with appropriate attributes."""
        super(RelationForm, self).__init__(*args, **kwargs)
        self.helper = RelationFormSetHelper()
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/relation/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        """Render proper form id by prepending 'id_relation_'."""
        form_id = 'id_relation_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        """Render form_id with quotes around it."""
        form_id = 'id_relation_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        """Describe meta properties of RelationForm."""

        model = Relation
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['type', 'value']
        labels = {'type': 'Relation type', 'value': 'Related to'}


class RelationValidationForm(forms.Form):
    """Validate RelationForm 'type' and 'value' CharFields."""

    type = forms.CharField(max_length=100)
    value = forms.CharField(max_length=500)


class SourceFormSetHelper(FormHelper):
    """Render layout for Source form including HTML5 valdiation and errors."""

    def __init__(self, *args, **kwargs):
        """Render layout for Source form including HTML5 valdiation and errors."""
        super(SourceFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = False
        self.layout = Layout(
            Fieldset('Source',
                     Field('derived_from', css_class=field_width),
                     ),
        )


class SourceForm(ModelForm):
    """Render Source model form with appropriate attributes."""

    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
        """Render Source model form with appropriate attributes."""
        super(SourceForm, self).__init__(*args, **kwargs)
        self.helper = SourceFormSetHelper()
        self.number = 0
        self.delete_modal_form = None
        self.allow_edit = allow_edit
        if res_short_id:
            self.action = "/hsapi/_internal/%s/source/add-metadata/" % res_short_id
        else:
            self.action = ""
        if not allow_edit:
            self.fields['derived_from'].widget.attrs['readonly'] = True
            self.fields['derived_from'].widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        """Render proper form id by prepending 'id_source_'."""
        form_id = 'id_source_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        """Render proper form id with quotes."""
        form_id = 'id_source_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        """Define meta properties for SourceForm."""

        model = Source
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['derived_from']


class SourceValidationForm(forms.Form):
    """Validate derived_from field from SourceForm."""

    derived_from = forms.CharField(max_length=300)


class IdentifierFormSetHelper(FormHelper):
    """Render layout for Identifier form including HTML5 valdiation and errors."""

    def __init__(self, *args, **kwargs):
        """Render layout for Identifier form including HTML5 valdiation and errors."""
        super(IdentifierFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = True
        self.layout = Layout(
            Fieldset('Identifier',
                     Field('name', css_class=field_width),
                     Field('url', css_class=field_width),
                     ),
        )


class IdentifierForm(ModelForm):
    """Render Identifier model form with appropriate attributes."""

    def __init__(self, res_short_id=None, *args, **kwargs):
        """Render Identifier model form with appropriate attributes."""
        super(IdentifierForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['name'].widget.attrs['style'] = "background-color:white;"
        self.fields['url'].widget.attrs['readonly'] = True
        self.fields['url'].widget.attrs['style'] = "background-color:white;"

        self.helper = IdentifierFormSetHelper()
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/identifier/add-metadata/" % res_short_id
        else:
            self.action = ""

    class Meta:
        """Define meta properties for IdentifierForm class."""

        model = Identifier
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'url']

    def clean(self):
        """Ensure that identifier name attribute is not blank."""
        data = self.cleaned_data
        if data['name'].lower() == 'hydroshareidentifier':
            raise forms.ValidationError("Identifier name attribute can't have a value "
                                        "of '{}'.".format(data['name']))
        return data


class FundingAgencyFormSetHelper(FormHelper):
    """Render layout for FundingAgency form."""

    def __init__(self, *args, **kwargs):
        """Render layout for FundingAgency form."""
        super(FundingAgencyFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = False
        self.layout = Layout(
            Fieldset('Funding Agency',
                     Field('agency_name', css_class=field_width),
                     Field('award_title', css_class=field_width),
                     Field('award_number', css_class=field_width),
                     Field('agency_url', css_class=field_width),
                     ),
        )


class FundingAgencyForm(ModelForm):
    """Render FundingAgency model form with appropriate attributes."""

    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
        """Render FundingAgency model form with appropriate attributes."""
        super(FundingAgencyForm, self).__init__(*args, **kwargs)
        self.helper = FundingAgencyFormSetHelper()
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/fundingagency/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    @property
    def form_id(self):
        """Render proper form id by prepending 'id_fundingagency_'."""
        form_id = 'id_fundingagency_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        """Render proper form id with quotes."""
        form_id = 'id_fundingagency_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        """Define meta properties of FundingAgencyForm class."""

        model = FundingAgency
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['agency_name', 'award_title', 'award_number', 'agency_url']
        labels = {'agency_name': 'Funding agency name', 'award_title': 'Title of the award',
                  'award_number': 'Award number', 'agency_url': 'Agency website'}


class FundingAgencyValidationForm(forms.Form):
    """Validate FundingAgencyForm with agency_name, award_title, award_number and agency_url."""

    agency_name = forms.CharField(required=True)
    award_title = forms.CharField(required=False)
    award_number = forms.CharField(required=False)
    agency_url = forms.URLField(required=False)


class BaseFormHelper(FormHelper):
    """Render non-repeatable element related forms."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 element_layout=None,  *args, **kwargs):
        """Render non-repeatable element related forms."""
        coverage_type = kwargs.pop('coverage', None)
        element_name_label = kwargs.pop('element_name_label', None)

        super(BaseFormHelper, self).__init__(*args, **kwargs)

        if res_short_id:
            self.form_method = 'post'
            self.form_tag = True
            if element_name.lower() == 'coverage':
                if coverage_type:
                    self.form_id = 'id-%s-%s' % (element_name.lower(), coverage_type)
                else:
                    self.form_id = 'id-%s' % element_name.lower()
            else:
                self.form_id = 'id-%s' % element_name.lower()

            if element_id:
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % \
                                   (res_short_id, element_name.lower(), element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % (res_short_id,
                                                                             element_name)
        else:
            self.form_tag = False

        # change the first character to uppercase of the element name
        element_name = element_name.title()
        if element_name_label:
            element_name = element_name_label

        if element_name == "Subject":
            element_name = "Keywords"
        elif element_name == "Description":
            element_name = "Abstract"
        if res_short_id and allow_edit:
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                                     HTML('<div style="margin-top:10px">'),
                                     HTML('<button type="button" '
                                          'class="btn btn-primary pull-right btn-form-submit" '
                                          'return false;">Save changes</button>'),
                                     HTML('</div>')
                                     ),
                         )  # TODO: TESTING
        else:
            self.form_tag = False
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                                     ),
                          )


class TitleValidationForm(forms.Form):
    """Validate Title form with value."""

    value = forms.CharField(max_length=300)


class SubjectsFormHelper(BaseFormHelper):
    """Render Subject form.

    This form handles multiple subject elements - this was not implemented as formset
    since we are providing one input field to enter multiple keywords (subjects) as comma
    separated values
    """

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        """Render subject form.

        The order in which the model fields are listed for the FieldSet is the order these
        fields will be displayed
        """
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                 )

        super(SubjectsFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                 element_name, layout,  *args, **kwargs)


class SubjectsForm(forms.Form):
    """Render Subjects model form with appropriate attributes."""

    value = forms.CharField(max_length=500,
                            label='',
                            widget=forms.TextInput(attrs={'placeholder': 'Keywords'}),
                            help_text='Enter each keyword separated by a comma.')

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render Subjects model form with appropriate attributes."""
        super(SubjectsForm, self).__init__(*args, **kwargs)
        self.helper = SubjectsFormHelper(allow_edit, res_short_id, element_id,
                                         element_name='subject')
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/subject/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"


class AbstractFormHelper(BaseFormHelper):
    """Render Abstract form."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        """Render Abstract form.

        The order in which the model fields are listed for the FieldSet is the order these
        fields will be displayed
        """
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('abstract', css_class=field_width),
                 )

        super(AbstractFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                 element_name, layout,  *args, **kwargs)


class AbstractForm(ModelForm):
    """Render Abstract model form with appropriate attributes."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render Abstract model form with appropriate attributes."""
        super(AbstractForm, self).__init__(*args, **kwargs)
        self.helper = AbstractFormHelper(allow_edit, res_short_id, element_id,
                                         element_name='description')
        if not allow_edit:
            self.fields['abstract'].widget.attrs['disabled'] = True
            self.fields['abstract'].widget.attrs['style'] = "background-color:white;"

    class Meta:
        """Describe meta properties of AbstractForm."""

        model = Description
        fields = ['abstract']
        exclude = ['content_object']
        labels = {'abstract': ''}


class AbstractValidationForm(forms.Form):
    """Validate Abstract form with abstract field."""

    abstract = forms.CharField(max_length=5000)


class RightsValidationForm(forms.Form):
    """Validate Rights form with statement and URL field."""

    statement = forms.CharField(required=False)
    url = forms.URLField(required=False, max_length=500)

    def clean(self):
        """Clean data and render proper error messages."""
        cleaned_data = super(RightsValidationForm, self).clean()
        statement = cleaned_data.get('statement', None)
        url = cleaned_data.get('url', None)
        if not statement and not url:
            self._errors['statement'] = ["A value for statement is missing"]
            self._errors['url'] = ["A value for Url is missing"]

        return self.cleaned_data


class CoverageTemporalFormHelper(BaseFormHelper):
    """Render Temporal Coverage form."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        """Render Temporal Coverage form.

        The order in which the model fields are listed for the FieldSet is the order these
        fields will be displayed
        """
        file_type = kwargs.pop('file_type', False)
        form_field_names = ['start', 'end']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        layout = Layout(*crispy_form_fields)

        kwargs['coverage'] = 'temporal'

        super(CoverageTemporalFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                         element_name, layout,  *args, **kwargs)


class CoverageTemporalForm(forms.Form):
    """Render Coverage Temporal Form."""

    start = forms.DateField(label='Start Date')
    end = forms.DateField(label='End Date')

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render Coverage Temporal Form."""
        file_type = kwargs.pop('file_type', False)
        super(CoverageTemporalForm, self).__init__(*args, **kwargs)
        self.helper = CoverageTemporalFormHelper(allow_edit, res_short_id, element_id,
                                                 element_name='Temporal Coverage',
                                                 file_type=file_type)
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/coverage/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True

    def clean(self):
        """Modify the form's cleaned_data dictionary."""
        is_form_errors = False
        super(CoverageTemporalForm, self).clean()
        start_date = self.cleaned_data.get('start', None)
        end_date = self.cleaned_data.get('end', None)
        if not start_date:
            self._errors['start'] = ["Data for start date is missing"]
            is_form_errors = True

        if not end_date:
            self._errors['end'] = ["Data for end date is missing"]
            is_form_errors = True

        if start_date > end_date:
            self._errors['end'] = ["End date should be date after the start date"]
            is_form_errors = True

        if is_form_errors:
            return self.cleaned_data

        if 'name' in self.cleaned_data:
            if len(self.cleaned_data['name']) == 0:
                del self.cleaned_data['name']

        self.cleaned_data['start'] = self.cleaned_data['start'].isoformat()
        self.cleaned_data['end'] = self.cleaned_data['end'].isoformat()
        self.cleaned_data['value'] = copy.deepcopy(self.cleaned_data)
        self.cleaned_data['type'] = 'period'
        if 'name' in self.cleaned_data:
            del self.cleaned_data['name']
        del self.cleaned_data['start']
        del self.cleaned_data['end']

        return self.cleaned_data


class CoverageSpatialFormHelper(BaseFormHelper):
    """Render layout for CoverageSpatial form."""

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,
                 *args, **kwargs):
        """Render layout for CoverageSpatial form."""
        file_type = kwargs.pop('file_type', False)

        layout = Layout()
        # the order in which the model fields are listed for the FieldSet is the order these
        # fields will be displayed
        layout.append(Field('type', id="id_{}_filetype".format('type') if file_type else
                            "id_{}".format('type')))
        form_field_names = ['name', 'projection', 'east', 'north', 'northlimit', 'eastlimit',
                            'southlimit', 'westlimit', 'units']
        crispy_form_fields = get_crispy_form_fields(form_field_names, file_type=file_type)
        for field in crispy_form_fields:
            layout.append(field)
        kwargs['coverage'] = 'spatial'
        super(CoverageSpatialFormHelper, self).__init__(allow_edit, res_short_id, element_id,
                                                        element_name, layout,  *args, **kwargs)


class CoverageSpatialForm(forms.Form):
    """Render CoverateSpatial form."""

    TYPE_CHOICES = (
        ('box', 'Box'),
        ('point', 'Point')
    )

    type = forms.ChoiceField(choices=TYPE_CHOICES,
                             widget=forms.RadioSelect(attrs={'class': 'inline'}), label='')
    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    projection = forms.CharField(max_length=100, required=False,
                                 label='Coordinate System/Geographic Projection')

    east = forms.DecimalField(label='Longitude', widget=forms.TextInput())
    north = forms.DecimalField(label='Latitude', widget=forms.TextInput())
    units = forms.CharField(max_length=50, label='Coordinate Units')
    northlimit = forms.DecimalField(label='North Latitude', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Longitude', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Latitude', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Longitude', widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        """Render CoverateSpatial form."""
        file_type = kwargs.pop('file_type', False)
        super(CoverageSpatialForm, self).__init__(*args, **kwargs)

        self.helper = CoverageSpatialFormHelper(allow_edit, res_short_id, element_id,
                                                element_name='Spatial Coverage',
                                                file_type=file_type)
        self.number = 0
        self.delete_modal_form = None
        if self.errors:
            self.errors.clear()
        if res_short_id:
            self.action = "/hsapi/_internal/%s/coverage/add-metadata/" % res_short_id
        else:
            self.action = ""

        if len(self.initial) > 0:
            self.initial['projection'] = 'WGS 84 EPSG:4326'
            self.initial['units'] = 'Decimal degrees'

        else:
            self.fields['type'].widget.attrs['checked'] = 'checked'
            self.fields['projection'].widget.attrs['value'] = 'WGS 84 EPSG:4326'
            self.fields['units'].widget.attrs['value'] = 'Decimal degrees'

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
        else:
            self.fields['projection'].widget.attrs['readonly'] = True
            self.fields['units'].widget.attrs['readonly'] = True
            if file_type:
                # add the 'data-map-item' attribute so that map interface can be used for editing
                # these fields
                self.fields['north'].widget.attrs['data-map-item'] = 'latitude'
                self.fields['east'].widget.attrs['data-map-item'] = 'longitude'
                self.fields['northlimit'].widget.attrs['data-map-item'] = 'northlimit'
                self.fields['eastlimit'].widget.attrs['data-map-item'] = 'eastlimit'
                self.fields['southlimit'].widget.attrs['data-map-item'] = 'southlimit'
                self.fields['westlimit'].widget.attrs['data-map-item'] = 'westlimit'

    def clean(self):
        """Modify the form's cleaned_data dictionary."""
        super(CoverageSpatialForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        spatial_coverage_type = temp_cleaned_data['type']
        is_form_errors = False
        if self.errors:
            self.errors.clear()
        if spatial_coverage_type == 'point':
            north = temp_cleaned_data.get('north', None)
            east = temp_cleaned_data.get('east', None)
            if not north and north != 0:
                self._errors['north'] = ["Data for north is missing"]
                is_form_errors = True
                del self.cleaned_data['north']

            if not east and east != 0:
                self._errors['east'] = ["Data for east is missing"]
                is_form_errors = True
                del self.cleaned_data['east']

            if is_form_errors:
                return self.cleaned_data

            if 'northlimit' in temp_cleaned_data:
                del temp_cleaned_data['northlimit']
            if 'eastlimit' in self.cleaned_data:
                del temp_cleaned_data['eastlimit']
            if 'southlimit' in temp_cleaned_data:
                del temp_cleaned_data['southlimit']
            if 'westlimit' in temp_cleaned_data:
                del temp_cleaned_data['westlimit']
            if 'uplimit' in temp_cleaned_data:
                del temp_cleaned_data['uplimit']
            if 'downlimit' in temp_cleaned_data:
                del temp_cleaned_data['downlimit']

            temp_cleaned_data['north'] = str(temp_cleaned_data['north'])
            temp_cleaned_data['east'] = str(temp_cleaned_data['east'])

        else:   # box type coverage
            if 'north' in temp_cleaned_data:
                del temp_cleaned_data['north']
            if 'east' in temp_cleaned_data:
                del temp_cleaned_data['east']
            if 'elevation' in temp_cleaned_data:
                del temp_cleaned_data['elevation']

            for limit in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
                limit_data = temp_cleaned_data.get(limit, None)
                # allow value of 0 to go through
                if not limit_data and limit_data != 0:
                    self._errors[limit] = ["Data for %s is missing" % limit]
                    is_form_errors = True
                    del self.cleaned_data[limit]

            if is_form_errors:
                return self.cleaned_data

            temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
            temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
            temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
            temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])

        del temp_cleaned_data['type']
        if 'projection' in temp_cleaned_data:
            if len(temp_cleaned_data['projection']) == 0:
                del temp_cleaned_data['projection']

        if 'name' in temp_cleaned_data:
            if len(temp_cleaned_data['name']) == 0:
                del temp_cleaned_data['name']

        self.cleaned_data['value'] = copy.deepcopy(temp_cleaned_data)

        if 'northlimit' in self.cleaned_data:
                del self.cleaned_data['northlimit']
        if 'eastlimit' in self.cleaned_data:
                del self.cleaned_data['eastlimit']
        if 'southlimit' in self.cleaned_data:
            del self.cleaned_data['southlimit']
        if 'westlimit' in self.cleaned_data:
            del self.cleaned_data['westlimit']
        if 'uplimit' in self.cleaned_data:
            del self.cleaned_data['uplimit']
        if 'downlimit' in self.cleaned_data:
            del self.cleaned_data['downlimit']
        if 'north' in self.cleaned_data:
            del self.cleaned_data['north']
        if 'east' in self.cleaned_data:
            del self.cleaned_data['east']
        if 'elevation' in self.cleaned_data:
            del self.cleaned_data['elevation']

        if 'name' in self.cleaned_data:
            del self.cleaned_data['name']

        if 'units' in self.cleaned_data:
            del self.cleaned_data['units']

        if 'zunits' in self.cleaned_data:
            del self.cleaned_data['zunits']

        if 'projection' in self.cleaned_data:
            del self.cleaned_data['projection']

        return self.cleaned_data


class LanguageValidationForm(forms.Form):
    """Validate LanguageValidation form with code attribute."""

    code = forms.CharField(max_length=3)


class ValidDateValidationForm(forms.Form):
    """Validate DateValidationForm with start_date and end_date attribute."""

    start_date = forms.DateField()
    end_date = forms.DateField()

    def clean(self):
        """Modify the form's cleaned data dictionary."""
        cleaned_data = super(ValidDateValidationForm, self).clean()
        start_date = cleaned_data.get('start_date', None)
        end_date = cleaned_data.get('end_date', None)
        if start_date and not end_date:
            self._errors['end_date'] = ["End date is missing"]

        if end_date and not start_date:
            self._errors['start_date'] = ["Start date is missing"]

        if not start_date and not end_date:
            del self._errors['start_date']
            del self._errors['end_date']

        if start_date and end_date:
            self.cleaned_data['type'] = 'valid'

        return self.cleaned_data


def get_crispy_form_fields(field_names, file_type=False):
    """Return a list of objects of type Field.

    :param field_names: list of form field names
    :param file_type: if true, then this is a metadata form for file type, otherwise, a form
    for resource
    :return: a list of Field objects
    """
    crispy_fields = []

    def get_field_id(field_name):
        if file_type:
            return "id_{}_filetype".format(field_name)
        return "id_{}".format(field_name)

    for field_name in field_names:
        crispy_fields.append(Field(field_name, css_class='form-control input-sm',
                                   id=get_field_id(field_name)))
    return crispy_fields
