__author__ = 'Pabitra'
import copy
from models import *
from django.forms import ModelForm, BaseFormSet, DateInput, Select, TextInput
from django.forms.models import inlineformset_factory, modelformset_factory, formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.bootstrap import *
import arrow
from django.contrib.admin.widgets import *
from django.forms.extras.widgets import SelectDateWidget
from django.utils.safestring import mark_safe
from functools import partial, wraps
from hydroshare import utils

class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class Helper(object):

    @classmethod
    def get_element_add_modal_form(cls, element_name, modal_form_context_name):
        modal_title = "Add %s" % element_name.title()
        layout = Layout(
                            HTML('<div class="modal fade" id="add-element-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                    '<div class="modal-dialog">'
                                        '<div class="modal-content">'),
                                            HTML('<form action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '),
                                            HTML('{% csrf_token %} '
                                            '<input name="resource-mode" type="hidden" value="edit"/>'
                                            '<div class="modal-header">'
                                                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'),
                                                HTML('<h4 class="modal-title" id="myModalLabel"> Add Element </h4>'),
                                            HTML('</div>'
                                            '<div class="modal-body">'
                                                '{% csrf_token %}'
                                                '<div class="form-group">'),
                                                   HTML('{% load crispy_forms_tags %} '
                                                       '{% crispy add_creator_modal_form %} '),
                                                    # '{% for link_form in add_creator_modal_form.profile_link_formset.forms %} '
                                                    #  '<div class="item_link" '
                                                    #  '{% crispy link_form %} '
                                                    #  '</div> {% endfor %} '
                                                HTML('</div>'
                                            '</div>'
                                            '<div class="modal-footer">'
                                                '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'
                                                '<button type="submit" class="btn btn-primary">Save changes</button>'
                                            '</div>'
                                            '</form>'
                                        '</div>'
                                    '</div>'
                                '</div>')
                        )

        layout[0] = HTML('<div class="modal fade" id="add-%s-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                    '<div class="modal-dialog">'
                                        '<div class="modal-content">' % element_name.lower())
        layout[1] = HTML('<form action="{{ %s.action }}" method="POST" enctype="multipart/form-data"> ' % modal_form_context_name)
        layout[3] = HTML('<h4 class="modal-title" id="myModalLabel"> {title} </h4>'.format(title=modal_title),)
        html_str = '{% load crispy_forms_tags %} {% crispy' + ' add_{element}_modal_form'.format(element= element_name.lower()) + ' %}'
        layout[5] = HTML(html_str)

        return layout


ModalDialogLayoutAddCreator = Helper.get_element_add_modal_form('Creator', 'add_creator_modal_form')

ModalDialogLayoutAddContributor = Helper.get_element_add_modal_form('Contributor', 'add_contributor_modal_form')

ModalDialogLayoutAddRelation = Helper.get_element_add_modal_form('Relation', 'add_relation_modal_form')

ModalDialogLayoutAddSource = Helper.get_element_add_modal_form('Source', 'add_source_modal_form')

CreatorLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                     '<div class="item form-group"> '
                                         '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                         '{% crispy form %} '
                                            '{{ form.profile_link_formset.management_form }} '
                                            '{% for link_form in form.profile_link_formset.forms %} '
                                                '<div class="item_link"> '
                                                    '{% crispy link_form %} '
                                                '</div>'
                                            '{% endfor %} '
                                        # '<div style="margin-top:10px"><a id="addLinkCreator" class="btn btn-success" disabled="disabled" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
                                        '<div class="row" style="margin-top:10px">'
                                            '<div class="col-md-10">'
                                                '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-creator-element-dialog_{{ form.number }}" value="Delete creator">'
                                            '</div>'
                                            '<div class="col-md-2">'
                                                '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save changes</button>'
                                            '</div>'
                                        '</div>'
                                        '{% crispy form.delete_modal_form %} '
                                        '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-creator" class="btn btn-success" data-toggle="modal" data-target="#add-creator-dialog">'
                                 '<i class="fa fa-plus"></i>Add another creator</a>'
                                 '</div>'
                            ),
                    )


ContributorLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in contributor_formset.forms %} '
                                     '<div class="item form-group"> '
                                         '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                         '{% crispy form %} '
                                            '{{ form.profile_link_formset.management_form }} '
                                            '{% for link_form in form.profile_link_formset.forms %} '
                                                '<div class="item_link"> '
                                                    '{% crispy link_form %} '
                                                '</div>'
                                            '{% endfor %} '
                                        # '<div style="margin-top:10px"><a id="addLinkContributor" class="btn btn-success" disabled="disabled" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
                                        '<div class="row" style="margin-top:10px">'
                                            '<div class="col-md-10">'
                                                '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-contributor-element-dialog_{{ form.number }}" value="Delete contributor">'
                                            '</div>'
                                            '<div class="col-md-2">'
                                                '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save changes</button>'
                                            '</div>'
                                        '</div>'
                                        '{% crispy form.delete_modal_form %} '
                                        '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-creator" class="btn btn-success" data-toggle="modal" data-target="#add-contributor-dialog">'
                                 '<i class="fa fa-plus"></i>Add another contributor</a>'
                                 '</div>'
                            ),
                    )

RelationLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in relation_formset.forms %} '
                                     '<div class="item form-group"> '
                                         '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                         '{% crispy form %} '
                                         '<div class="row" style="margin-top:10px">'
                                            '<div class="col-md-10">'
                                                '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-relation-element-dialog_{{ form.number }}" value="Delete relation">'
                                            '</div>'
                                            '<div class="col-md-2">'
                                                '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save changes</button>'
                                            '</div>'
                                        '</div>'
                                        '{% crispy form.delete_modal_form %} '
                                        '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-relation" class="btn btn-success" data-toggle="modal" data-target="#add-relation-dialog">'
                                 '<i class="fa fa-plus"></i>Add another relation</a>'
                                 '</div>'
                            ),
                    )


SourceLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in source_formset.forms %} '
                                     '<div class="item form-group"> '
                                         '<form id={{form.form_id}} action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                         '{% crispy form %} '
                                         '<div class="row" style="margin-top:10px">'
                                            '<div class="col-md-10">'
                                                '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-source-element-dialog_{{ form.number }}" value="Delete source">'
                                            '</div>'
                                            '<div class="col-md-2">'
                                                '<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit({{ form.form_id_button }}); return false;">Save changes</button>'
                                            '</div>'
                                        '</div>'
                                        '{% crispy form.delete_modal_form %} '
                                        '</form> '
                                    '</div> '
                                '{% endfor %}'
                            ),

                            HTML('<div style="margin-top:10px">'
                                 '<p><a id="add-source" class="btn btn-success" data-toggle="modal" data-target="#add-source-dialog">'
                                 '<i class="fa fa-plus"></i>Add another source</a>'
                                 '</div>'
                            ),
                    )


# the 1st and the 3rd HTML layout objects get replaced in MetaDataElementDeleteForm class
def _get_modal_confirm_delete_matadata_element():
    layout = Layout(
                    HTML('<div class="modal fade" id="delete-metadata-element-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'),
                            HTML('<div class="modal-dialog">'
                                '<div class="modal-content">'
                                    '<div class="modal-header">'
                                        '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                        '<h4 class="modal-title" id="myModalLabel">Delete metadata element</h4>'
                                    '</div>'
                                    '<div class="modal-body">'
                                        '<strong>Are you sure you want to delete this metadata element?</strong>'

                                    '</div>'
                                    '<div class="modal-footer">'
                                        '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>'),
                                        HTML('<a type="button" class="btn btn-danger" href="">Delete</a>'),
                                    HTML('</div>'
                                '</div>'
                            '</div>'
                        '</div>'),
                    )
    return layout


class MetaDataElementDeleteForm(forms.Form):
    def __init__(self, res_short_id, element_name, element_id , *args, **kwargs):
        super(MetaDataElementDeleteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.delete_element_action = '"/hsapi/_internal/%s/%s/%s/delete-metadata/"' % (res_short_id, element_name, element_id)
        self.helper.layout = _get_modal_confirm_delete_matadata_element()
        self.helper.layout[0] = HTML('<div class="modal fade" id="delete-%s-element-dialog_%s" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">' % (element_name, element_id))
        self.helper.layout[2] = HTML('<a type="button" class="btn btn-danger" href=%s>Delete</a>' % self.delete_element_action)
        self.helper.form_tag = False

class ExtendedMetadataForm(forms.Form):
    def __init__(self, resource_mode='edit', extended_metadata_layout=None, *args, **kwargs):
        super(ExtendedMetadataForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        # self.helper.form_method = 'post'
        # self.helper.form_action = "/hsapi/_internal/create-resource/"
        self.helper.form_tag = False
        self.helper.layout = extended_metadata_layout

class MetaDataForm(forms.Form):
    def __init__(self, resource_mode='edit', extended_metadata_layout=None, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)

        creator_layout = CreatorLayoutEdit
        contributor_layout = ContributorLayoutEdit
        relation_layout = RelationLayoutEdit
        source_layout = SourceLayoutEdit
        #identifier_layout = IdentifierLayoutView
        #format_layout = FormatLayoutView
        modal_dialog_add_creator = ModalDialogLayoutAddCreator
        modal_dialog_add_contributor = ModalDialogLayoutAddContributor
        modal_dialog_add_relation = ModalDialogLayoutAddRelation
        modal_dialog_add_source = ModalDialogLayoutAddSource

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = "/hsapi/_internal/create-resource/"
        self.helper.form_tag = False

        html_title_layout = HTML('<div class="form-group" id="title"> '
                                    '{% load crispy_forms_tags %} '
                                    '{% crispy title_form %} '
                                 '</div>')

        ag_abstract_layout = AccordionGroup('Abstract (required)',
                                            HTML('<div class="form-group" id="abstract"> '
                                                '{% load crispy_forms_tags %} '
                                                '{% crispy abstract_form %} '
                                                '</div>'),
                                          )

        ag_creators_layout = AccordionGroup('Creators (required)',
                                            HTML("<div class='form-group' id='creator'>"),
                                            HTML("{{ creator_formset.management_form }}"),
                                            creator_layout,
                                            HTML("</div>"),
                                        )

        ag_contributors_layout = AccordionGroup('Contributors (optional)',
                                                HTML("<div class='form-group' id='contributor'>"),
                                                HTML("{{ contributor_formset.management_form }}"),
                                                contributor_layout,
                                                HTML("</div>"),
                                            )

        ag_temporal_coverage_layout = AccordionGroup('Temporal Coverage (optional)',
                                                        HTML('<div class="form-group" id="coverage-temporal"> '
                                                                 '{% load crispy_forms_tags %} '
                                                                 '{% crispy coverage_temporal_form %} '
                                                             '</div>'),
                                                    )

        ag_spatial_coverage_layout = AccordionGroup('Spatial Coverage (optional)',
                                                    HTML('<div class="form-group" id="coverage-spatial"> '
                                                            '{% load crispy_forms_tags %} '
                                                            '{% crispy coverage_spatial_form %} '
                                                         '</div>'),
                                                )
        ag_language_layout = AccordionGroup('Language (optional)',
                                                HTML('<div class="form-group" id="language"> '
                                                        '{% load crispy_forms_tags %} '
                                                        '{% crispy language_form %} '
                                                     '</div>'),
                                            )

        ag_keywords_layout = AccordionGroup('Keywords (required)',
                                                 HTML('<div class="form-group" id="subjects"> '
                                                        '{% load crispy_forms_tags %} '
                                                        '{% crispy subjects_form %} '
                                                      '</div>'),
                                            )

        ag_rights_layout = AccordionGroup('Rights (required)',
                                            HTML('<div class="form-group" id="source"> '
                                                    '{% load crispy_forms_tags %} '
                                                    '{% crispy rights_form %} '
                                                 '</div>'),
                                        )

        ag_sources_layout = AccordionGroup('Sources (optional)',
                                            HTML("<div class='form-group' id='source'>"),
                                            HTML("{{ source_formset.management_form }}"),
                                            source_layout,
                                            HTML("</div>"),
                                        )

        ag_relations_layout = AccordionGroup('Relations (optional)',
                                            HTML("<div class='form-group' id='relation'>"),
                                            HTML("{{ relation_formset.management_form }}"),
                                            relation_layout,
                                            HTML("</div>"),
                                        )

        if extended_metadata_layout:
            layout = Layout(
                    TabHolder(
                        Tab("Core Metadata",
                            html_title_layout,

                            Accordion(
                                ag_abstract_layout,

                                ag_creators_layout,

                                ag_contributors_layout,

                                # AccordionGroup('Valid date (optional)',
                                #     HTML('<div class="form-group" id="validdate"> '
                                #             '{% load crispy_forms_tags %} '
                                #             '{% crispy valid_date_form %} '
                                #          '</div>'),
                                # ),

                                ag_temporal_coverage_layout,

                                ag_spatial_coverage_layout,

                                ag_language_layout,

                                ag_keywords_layout,

                                ag_rights_layout,

                                ag_sources_layout,

                                ag_relations_layout,

                            ),
                        ),

                        # Specific resource type app needs to provide the crispy form Layout object: extended_metadata_layout
                        Tab("Extended Metadata",
                            extended_metadata_layout,
                        ),
                    ),
                    modal_dialog_add_creator,
                    modal_dialog_add_contributor,
                    modal_dialog_add_relation,
                    modal_dialog_add_source,
                )
        else:
            layout = Layout(
                            html_title_layout,

                            Accordion(
                                ag_abstract_layout,

                                ag_creators_layout,

                                ag_contributors_layout,

                                ag_temporal_coverage_layout,

                                ag_spatial_coverage_layout,

                                ag_language_layout,

                                ag_keywords_layout,

                                ag_rights_layout,

                                ag_sources_layout,

                                ag_relations_layout,

                            ),
                            modal_dialog_add_creator,
                            modal_dialog_add_contributor,
                            modal_dialog_add_relation,
                            modal_dialog_add_source,
                        )


        self.helper.layout = layout


class ProfileLinksFormSetHelper(FormHelper):
    def __init__(self, link_for, *args, **kwargs):
        super(ProfileLinksFormSetHelper, self).__init__(*args, **kwargs)

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        if link_for == 'creator':
            self.delete_btn_class = 'btn-danger delete-link-creator'
        else:
            self.delete_btn_class = 'btn-danger delete-link-contributor'

        link_delete_button = StrictButton('Delete Link', css_class=self.delete_btn_class)

        self.layout = Layout(
            Fieldset('External Profile Link',
                     Field('type', css_class=field_width),
                     Field('url', css_class=field_width),
                     HTML('<div style="margin-top:10px"></div>')
                     ),
            ButtonHolder(
                link_delete_button,
            )
        )


class ProfileLinksForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileLinksForm, self).__init__(*args, **kwargs)
        self.helper = ProfileLinksFormSetHelper(link_for='creator')

    class Meta:
        model = ExternalProfileLink
        #type = forms.ModelChoiceField(queryset=["ResearchID", "ResearchGateID"])
        fields = ['type', 'url']
        TYPE_CHOICES = (
            ('', '___________'),
            ('ResearchID', 'Research ID'),
            ('ResearchGateID', 'Research Gate ID')
        )
        widgets = {'type': Select(choices=TYPE_CHOICES, attrs={'class': 'select'}),}


class BaseProfileLinkFormSet(BaseFormSet):
    def get_metadata(self):
        links_data = []
        for form in self.forms:
            link_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if len(link_data) > 0:
                links_data.append(link_data)

        return {'profile_links': links_data}


ProfileLinksFormset = formset_factory(ProfileLinksForm, formset=BaseProfileLinkFormSet)


class CreatorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(CreatorFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, *args, **kwargs):
        if 'initial' in kwargs:
            if 'description' in kwargs['initial']:
                if kwargs['initial']['description']:
                    kwargs['initial']['description'] = utils.current_site_url() + kwargs['initial']['description']
        super(PartyForm, self).__init__(*args, **kwargs)
        self.profile_link_formset = None
        self.number = 0
        
    class Meta:
        model = Party
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage']

        # TODO: field labels and widgets types to be specified
        labels = {'description': 'HydroShare User Identifier (URL)'}


class CreatorForm(PartyForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()
        self.profile_link_formset = ProfileLinksFormset(prefix='creator_links')
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
        form_id = 'id_creator_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_creator_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Creator
        fields = PartyForm.Meta.fields
        fields.append("order")
        labels = PartyForm.Meta.labels


class PartyValidationForm(forms.Form):
    description = forms.URLField(required=False, validators=[validate_user_url])
    name = forms.CharField(max_length=100)
    organization = forms.CharField(max_length=200, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=250, required=False)
    phone = forms.CharField(max_length=25, required=False)
    homepage = forms.URLField(required=False)

    def clean_description(self):
        user_absolute_url = self.cleaned_data['description']
        if user_absolute_url:
            url_parts = user_absolute_url.split('/')
            return '/user/{user_id}/'.format(user_id=url_parts[4])
        return user_absolute_url

    def clean(self):
        cleaned_data = super(PartyValidationForm, self).clean()
        name = cleaned_data.get('name', None)
        if not name or len(name.strip()) == 0:
            self._errors['name'] = ["A value for name is missing"]

        return self.cleaned_data

class CreatorValidationForm(PartyValidationForm):
    order = forms.IntegerField(required=False)


class ContributorValidationForm(PartyValidationForm):
    pass


class BaseCreatorFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super(BaseCreatorFormSet, self).add_fields(form, index)

        # create the nested profile link formset
        form.profile_link_formset = ProfileLinksFormset(prefix='creator_links-%s' % index)

    def get_metadata(self):
        creators_data = []
        for form in self.forms:
            creator_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if form.profile_link_formset.is_valid():
                profile_link_dict = form.profile_link_formset.get_metadata()
                if len(profile_link_dict['profile_links']) > 0:
                    creator_data['profile_links'] = profile_link_dict['profile_links']

            creators_data.append({'creator': creator_data})

        return creators_data


class ContributorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ContributorFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.helper = ContributorFormSetHelper()
        self.profile_link_formset = ProfileLinksFormset(prefix='contributor_links')
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
        form_id = 'id_contributor_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_contributor_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Contributor
        fields = PartyForm.Meta.fields
        labels = PartyForm.Meta.labels
        if 'order' in fields:
            fields.remove('order')


class BaseContributorFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super(BaseContributorFormSet, self).add_fields(form, index)

        # create the nested profile link formset
        form.profile_link_formset = ProfileLinksFormset(prefix='contributor_links-%s' % index)

    def get_metadata(self):
        contributors_data = []
        for form in self.forms:
            contributor_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if len(contributor_data) > 0:
                if form.profile_link_formset.is_valid():
                    profile_link_dict = form.profile_link_formset.get_metadata()
                    if len(profile_link_dict['profile_links']) > 0:
                        contributor_data['profile_links'] = profile_link_dict['profile_links']

                contributors_data.append({'contributor': contributor_data})

        return contributors_data


class RelationFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(RelationFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
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
        form_id = 'id_relation_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_relation_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Relation
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['type', 'value']
        labels = {'type': 'Relation type', 'value': 'Related to'}


class RelationValidationForm(forms.Form):
    type = forms.CharField(max_length=100)
    value = forms.CharField(max_length=500)


class SourceFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(SourceFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
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
        form_id = 'id_source_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_source_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = Source
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['derived_from']


class SourceValidationForm(forms.Form):
    derived_from = forms.CharField(max_length=300)



class IdentifierFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(IdentifierFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, res_short_id=None, *args, **kwargs):
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
        model = Identifier
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'url']


class FormatFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(FormatFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        self.form_show_errors = True
        self.error_text_inline = True
        self.html5_required = True
        self.layout = Layout(
            Fieldset('Format/MIME Type',
                     Field('value', css_class=field_width),
                     ),
        )


class FormatForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
        super(FormatForm, self).__init__(*args, **kwargs)
        self.fields['value'].widget.attrs['readonly'] = True
        self.fields['value'].widget.attrs['style'] = "background-color:white;"

        self.helper = FormatFormSetHelper()
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/format/add-metadata/" % res_short_id
        else:
            self.action = ""

    class Meta:
        model = Format
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['value']
        labels = {'value': 'Mime type'}


class FundingAgencyFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(FundingAgencyFormSetHelper, self).__init__(*args, **kwargs)
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
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
    def __init__(self, allow_edit=True, res_short_id=None, *args, **kwargs):
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
        form_id = 'id_fundingagency_%s' % self.number
        return form_id

    @property
    def form_id_button(self):
        form_id = 'id_fundingagency_%s' % self.number
        return "'" + form_id + "'"

    class Meta:
        model = FundingAgency
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['agency_name', 'award_title', 'award_number', 'agency_url']
        labels = {'agency_name': 'Funding agency name', 'award_title': 'Title of the award',
                  'award_number': 'Award number', 'agency_url': 'Agency website' }


class FundingAgencyValidationForm(forms.Form):
    agency_name = forms.CharField(required=True)
    award_title = forms.CharField(required=False)
    award_number = forms.CharField(required=False)
    agency_url = forms.URLField(required=False)



# Non repeatable element related forms
class BaseFormHelper(FormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None, element_layout=None,  *args, **kwargs):
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
                self.form_action = "/hsapi/_internal/%s/%s/%s/update-metadata/" % (res_short_id, element_name.lower(), element_id)
            else:
                self.form_action = "/hsapi/_internal/%s/%s/add-metadata/" % (res_short_id, element_name)
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
        form_id = "'" + self.form_id + "'"
        if res_short_id and allow_edit:
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                                     HTML('<div style="margin-top:10px">'),
                                     HTML('<button type="button" class="btn btn-primary pull-right" onclick="metadata_update_ajax_submit(%s); return false;">Save changes</button>' % form_id),
                                     HTML('</div>')
                            ),
                         )
        else:
            self.form_tag = False
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                            ),
                          )

class TitleFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                 )

        super(TitleFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class TitleForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(TitleForm, self).__init__(*args, **kwargs)
        self.helper = TitleFormHelper(allow_edit, res_short_id, element_id, element_name='title')
        if not allow_edit:
            self.fields['value'].widget.attrs['disabled'] = True
            self.fields['value'].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Title
        fields = ['value']
        exclude = ['content_object']
        labels = {'value': ''}


class TitleValidationForm(forms.Form):
    value = forms.CharField(max_length=300)


# This form handles multiple subject elements - this was not implemented as formset
# since we are providing one input field to enter multiple keywords (subjects) as comma separated values
class SubjectsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                 )

        super(SubjectsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class SubjectsForm(forms.Form):
    value = forms.CharField(max_length=500,
                            label='',
                            widget=forms.TextInput(attrs={'placeholder': 'Keywords'}),
                            help_text='Enter each keyword separated by a comma.')

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(SubjectsForm, self).__init__(*args, **kwargs)
        self.helper = SubjectsFormHelper(allow_edit, res_short_id, element_id, element_name='subject')
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
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('abstract', css_class=field_width),
                 )

        super(AbstractFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class AbstractForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(AbstractForm, self).__init__(*args, **kwargs)
        self.helper = AbstractFormHelper(allow_edit, res_short_id, element_id, element_name='description')
        if not allow_edit:
            self.fields['abstract'].widget.attrs['disabled'] = True
            self.fields['abstract'].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Description
        fields = ['abstract']
        exclude = ['content_object']
        labels = {'abstract': ''}


class AbstractValidationForm(forms.Form):
    abstract = forms.CharField(max_length=5000)


class RightsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        if allow_edit:
            select_element_start_tag = HTML('<select id="select_license" class="form-control"> ')
        else:
            select_element_start_tag = HTML('<select id="select_license" class="form-control" readonly="True"> ')

        layout = Layout(
                        HTML('<p>Information about rights held in and over the HydroShare resource. (e.g. Creative commons Attribution License)</p>'),
                        HTML('<label class="control-label" for="select_license"> Select a license </label> '),
                        select_element_start_tag,
                        HTML('<option value="http://creativecommons.org/licenses/by/4.0/">Creative Commons Attribution CC BY</option> '
                                '<option value="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike CC BY-SA</option> '
                                '<option value="http://creativecommons.org/licenses/by-nd/4.0/">Creative Commons Attribution-NoDerivs CC BY-ND</option> '
                                '<option value="http://creativecommons.org/licenses/by-nc-sa/4.0/">Creative Commons Attribution-NoCommercial-ShareAlike CC BY-NC-SA</option> '
                                '<option value="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons Attribution-NoCommercial CC BY-NC</option> '
                                '<option value="http://creativecommons.org/licenses/by-nc-nd/4.0/">Creative Commons Attribution-NoCommercial-NoDerivs CC BY-NC-ND</option> '
                                '<option value="other">Other</option> '
                            '</select>'),

                        Field('statement', css_class=field_width),
                        Field('url', css_class=field_width),
                 )

        super(RightsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class RightsForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(RightsForm, self).__init__(*args, **kwargs)
        self.helper = RightsFormHelper(allow_edit, res_short_id, element_id, element_name='rights')

        self.fields['statement'].widget.attrs['rows'] = 3

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"
        elif len(self.initial) > 0:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Rights
        fields = ['statement', 'url']
        exclude = ['content_object']
        help_texts = {'url': 'A value for Statement or Url is required.'}


class RightsValidationForm(forms.Form):
    statement = forms.CharField(required=False)
    url = forms.URLField(required=False, max_length=500)

    def clean(self):
        cleaned_data = super(RightsValidationForm, self).clean()
        statement = cleaned_data.get('statement', None)
        url = cleaned_data.get('url', None)
        if not statement and not url:
            self._errors['statement'] = ["A value for statement is missing"]
            self._errors['url'] = ["A value for Url is missing"]

        return self.cleaned_data


class CoverageTemporalFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('type', css_class=field_width),
                        #Field('name', css_class=field_width),
                        Field('start', css_class=field_width),
                        Field('end', css_class=field_width),
                 )

        kwargs['coverage'] = 'temporal'

        super(CoverageTemporalFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class CoverageTemporalForm(forms.Form):
    #name = forms.CharField(max_length=200, required=False, label='Name', help_text='e.g., Period of record.')
    start = forms.DateField(label='Start Date')
    end = forms.DateField(label='End Date')

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CoverageTemporalForm, self).__init__(*args, **kwargs)
        self.helper = CoverageTemporalFormHelper(allow_edit, res_short_id, element_id, element_name='coverage')
        self.number = 0
        self.delete_modal_form = None
        if res_short_id:
            self.action = "/hsapi/_internal/%s/coverage/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    def clean(self):
        # modify the form's cleaned_data dictionary
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
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('type'),
                        Field('name', css_class=field_width),
                        Field('projection', css_class=field_width),
                        Field('east', css_class=field_width),
                        Field('north', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('units', css_class=field_width),
                        #Field('uplimit', css_class=field_width),
                        #Field('downlimit', css_class=field_width),
                        #Field('elevation', css_class=field_width),
                        #Field('zunits', css_class=field_width),
                 )

        kwargs['coverage'] = 'spatial'
        super(CoverageSpatialFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class CoverageSpatialForm(forms.Form):
    TYPE_CHOICES = (
        ('box', 'Box'),
        ('point', 'Point')
    )
    #type = forms.CharField(max_length=20, widget=Select(choices=TYPE_CHOICES, attrs={'class': 'select'}))
    type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.RadioSelect(renderer=HorizontalRadioRenderer), label='')
    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    projection = forms.CharField(max_length=100, required=False, label='Coordinate System/Geographic Projection')

    east = forms.DecimalField(label='Longitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    north = forms.DecimalField(label='Latitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    units = forms.CharField(max_length=50, label='Coordinate Units')
    #elevation = forms.DecimalField(required=False, widget=forms.TextInput())
    #zunits = forms.CharField(max_length=50, required=False, label='Elevation Units', help_text='e.g., meters')
    northlimit = forms.DecimalField(label='North Latitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    eastlimit = forms.DecimalField(label='East Longitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    southlimit = forms.DecimalField(label='South Latitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    westlimit = forms.DecimalField(label='West Longitude (WGS 84 decimal degrees)', widget=forms.TextInput())
    #uplimit = forms.DecimalField(required=False, label='Up Limit', widget=forms.TextInput())
    #downlimit = forms.DecimalField(required=False, label='Down Limit', widget=forms.TextInput())

    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(CoverageSpatialForm, self).__init__(*args, **kwargs)
        self.helper = CoverageSpatialFormHelper(allow_edit, res_short_id, element_id, element_name='coverage')
        self.number = 0
        self.delete_modal_form = None
        self.errors.clear()
        if res_short_id:
            self.action = "/hsapi/_internal/%s/coverage/add-metadata/" % res_short_id
        else:
            self.action = ""

        if len(self.initial) == 1:
            self.initial['projection'] = 'WGS 84 EPSG:4326'
            self.initial['units'] = 'Decimal degrees'

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"
        else:
            self.fields['projection'].widget.attrs['readonly'] = True
            self.fields['projection'].widget.attrs['style'] = "background-color:white;"
            self.fields['units'].widget.attrs['readonly'] = True
            self.fields['units'].widget.attrs['style'] = "background-color:white;"

    def clean(self):
        # modify the form's cleaned_data dictionary
        super(CoverageSpatialForm, self).clean()
        temp_cleaned_data = copy.deepcopy(self.cleaned_data)
        spatial_coverage_type = temp_cleaned_data['type']
        is_form_errors = False
        if spatial_coverage_type == 'point':
            north = temp_cleaned_data.get('north', None)
            east = temp_cleaned_data.get('east', None)
            if not north:
                self._errors['north'] = ["Data for north is missing"]
                is_form_errors = True
                del self.cleaned_data['north']

            if not east:
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


class LanguageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('code', css_class=field_width),
                 )

        super(LanguageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class LanguageForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(LanguageForm, self).__init__(*args, **kwargs)
        self.helper = LanguageFormHelper(allow_edit, res_short_id, element_id, element_name='language')
        if len(self.initial) == 0:
            self.initial['code'] = 'eng'

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Language
        fields = ['code']
        exclude = ['content_object']
        labels = {'code': 'Language name'}

class LanguageValidationForm(forms.Form):
    code = forms.CharField(max_length=3)


class ValidDateFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm datepicker'
        layout = Layout(
                        HTML('<p>Date range over which this resource is valid.</p>'),
                        Field('start_date', css_class=field_width),
                        Field('end_date', css_class=field_width),
                 )

        super(ValidDateFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ValidDateForm(ModelForm):
    def __init__(self, allow_edit=True, res_short_id=None, element_id=None, *args, **kwargs):
        super(ValidDateForm, self).__init__(*args, **kwargs)
        self.helper = ValidDateFormHelper(allow_edit, res_short_id, element_id, element_name='date')

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Date
        fields = ['start_date', 'end_date']
        exclude = ['content_object']
        labels = {'start_date': 'Start date', 'end_date': 'End date*'}
        widgets = {'start_date': DateInput(attrs={'class': 'datepicker', 'data-date-format': 'yyyy/mm/dd',}), 'end_date': DateInput(attrs={'class': 'datepicker', 'data-date-format': 'yyyy/mm/dd',})}

class ValidDateValidationForm(forms.Form):
    start_date = forms.DateField()
    end_date = forms.DateField()

    def clean(self):
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
