__author__ = 'Pabitra'
import copy
from models import *
from django.forms import ModelForm, BaseFormSet, DateInput, Select, TextInput
from django.forms.models import inlineformset_factory, modelformset_factory, formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.bootstrap import *
import arrow
from django.forms.extras.widgets import SelectDateWidget
from django.utils.safestring import mark_safe
from functools import partial, wraps


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))

ModalDialogLayoutAddCreator = Layout(
                            HTML('<div class="modal fade" id="add-creator-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                    '<div class="modal-dialog">'
                                        '<div class="modal-content">'
                                            '<form action="{{ add_creator_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
                                            '<div class="modal-header">'
                                                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                '<h4 class="modal-title" id="myModalLabel">Add Creator</h4>'
                                            '</div>'
                                            '<div class="modal-body">'
                                                '{% csrf_token %}'
                                                '<div class="form-group">'
                                                    '{% load crispy_forms_tags %} '
                                                    '{% crispy add_creator_modal_form %} '
                                                    # '{% for link_form in add_creator_modal_form.profile_link_formset.forms %} '
                                                    #  '<div class="item_link" '
                                                    #  '{% crispy link_form %} '
                                                    #  '</div> {% endfor %} '
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

ModalDialogLayoutAddContributor = Layout(
                            HTML('<div class="modal fade" id="add-contributor-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                    '<div class="modal-dialog">'
                                        '<div class="modal-content">'
                                            '<form action="{{ add_contributor_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
                                            '<div class="modal-header">'
                                                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                '<h4 class="modal-title" id="myModalLabel">Add Contributor</h4>'
                                            '</div>'
                                            '<div class="modal-body">'
                                                '{% csrf_token %}'
                                                '<div class="form-group">'
                                                    '{% load crispy_forms_tags %} '
                                                    '{% crispy add_contributor_modal_form %} '
                                                    # '{% for link_form in add_creator_modal_form.profile_link_formset.forms %} '
                                                    # '<div class="item_link" '
                                                    # '{% crispy link_form %} '
                                                    # '</div> {% endfor %} '
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

ModalDialogLayoutAddRelation = Layout(
                                HTML('<div class="modal fade" id="add-relation-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                        '<div class="modal-dialog">'
                                            '<div class="modal-content">'
                                                '<form action="{{ add_relation_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
                                                '<div class="modal-header">'
                                                    '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                    '<h4 class="modal-title" id="myModalLabel">Add Relation</h4>'
                                                '</div>'
                                                '<div class="modal-body">'
                                                    '{% csrf_token %}'
                                                    '<div class="form-group">'
                                                        '{% load crispy_forms_tags %} '
                                                        '{% crispy add_relation_modal_form %} '
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

ModalDialogLayoutAddSource = Layout(
                                HTML('<div class="modal fade" id="add-source-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                        '<div class="modal-dialog">'
                                            '<div class="modal-content">'
                                                '<form action="{{ add_source_modal_form.action }}" method="POST" enctype="multipart/form-data"> '
                                                '<div class="modal-header">'
                                                    '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                    '<h4 class="modal-title" id="myModalLabel">Add Source</h4>'
                                                '</div>'
                                                '<div class="modal-body">'
                                                    '{% csrf_token %}'
                                                    '<div class="form-group">'
                                                        '{% load crispy_forms_tags %} '
                                                        '{% crispy add_source_modal_form %} '
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

CreatorLayoutNew = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '{{ form.profile_link_formset.management_form }} '
                                     '{% for link_form in form.profile_link_formset.forms %} '
                                        '<div class="item_link"> '
                                            '{% crispy link_form %} '
                                        '</div> '
                                     '{% endfor %} '
                                     '<div style="margin-top:10px"><a id="addLinkCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
                                     '<div style="margin-top:10px"><input class="delete-creator btn-danger btn btn-md" type="button" value="Delete creator"></div>'
                                     '</div> '
                                 '{% endfor %}'
                                ),
                            HTML('<div style="margin-top:10px"><a id="addCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another creator</a></div>'),
                        )

CreatorLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '{{ form.profile_link_formset.management_form }} '
                                     '{% for link_form in form.profile_link_formset.forms %} '
                                        '<div class="item_link"> '
                                            '{% crispy link_form %} '
                                        '</div> '
                                     '{% endfor %} '
                                     '</div> '
                                 '{% endfor %}'
                                ),
                        )


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
                                        '<div style="margin-top:10px"><a id="addLinkCreator" class="btn btn-success" disabled="disabled" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
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

ContributorLayoutNew = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in contributor_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '{{ form.profile_link_formset.management_form }} '
                                     '{% for link_form in form.profile_link_formset.forms %} '
                                        '<div class="item_link"> '
                                            '{% crispy link_form %} '
                                        '</div> '
                                     '{% endfor %} '
                                     '<div style="margin-top:10px"><a id="addLinkContributor" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
                                     '<div style="margin-top:10px"><input class="delete-creator btn-danger btn btn-md" type="button" value="Delete contributor"></div>'
                                     '</div> '
                                 '{% endfor %}'
                                ),
                            HTML('<div style="margin-top:10px"><a id="addContributor" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another contributor</a></div>'),
                        )

ContributorLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in contributor_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '{{ form.profile_link_formset.management_form }} '
                                     '{% for link_form in form.profile_link_formset.forms %} '
                                        '<div class="item_link"> '
                                            '{% crispy link_form %} '
                                        '</div> '
                                     '{% endfor %} '
                                     '</div> '
                                 '{% endfor %}'
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
                                        '<div style="margin-top:10px"><a id="addLinkContributor" class="btn btn-success" disabled="disabled" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
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


RelationLayoutNew = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in relation_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '<div style="margin-top:10px"><input class="delete-relation btn-danger btn btn-md" type="button" value="Delete relation"></div>'
                                     '</div> '
                                 '{% endfor %}'
                                ),
                            HTML('<div style="margin-top:10px"><a id="addRelation" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another relation</a></div>'),
                        )

RelationLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in relation_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '</div> '
                                 '{% endfor %}'
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


SourceLayoutNew = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in source_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '<div style="margin-top:10px"><input class="delete-source btn-danger btn btn-md" type="button" value="Delete source"></div>'
                                     '</div> '
                                 '{% endfor %}'
                                ),
                            HTML('<div style="margin-top:10px"><a id="addSource" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another source</a></div>'),
                        )

SourceLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in source_formset.forms %} '
                                     '<div class="item"> '
                                     '{% crispy form %} '
                                     '</div> '
                                 '{% endfor %}'
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

IdentifierLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in identifier_formset.forms %} '
                                    '{% crispy form %} '
                                '{% endfor %}'
                            ),
                    )

FormatLayoutView = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in format_formset.forms %} '
                                    '{% crispy form %} '
                                '{% endfor %}'
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


class MetaDataForm(forms.Form):
    def __init__(self, resource_mode='view', extended_metadata_layout=None, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)
        if not extended_metadata_layout:
            extended_metadata_layout = HTML('<h3>No extended metadata for this resource.</h3>')

        if resource_mode == 'edit':
            creator_layout = CreatorLayoutEdit
            contributor_layout = ContributorLayoutEdit
            relation_layout = RelationLayoutEdit
            source_layout = SourceLayoutEdit
            identifier_layout = IdentifierLayoutView
            format_layout = FormatLayoutView
            modal_dialog_add_creator = ModalDialogLayoutAddCreator
            modal_dialog_add_contributor = ModalDialogLayoutAddContributor
            modal_dialog_add_relation = ModalDialogLayoutAddRelation
            modal_dialog_add_source = ModalDialogLayoutAddSource
        else:   # view mode
            creator_layout = CreatorLayoutView
            contributor_layout = ContributorLayoutView
            relation_layout = RelationLayoutView
            source_layout = SourceLayoutView
            identifier_layout = IdentifierLayoutView
            format_layout = FormatLayoutView
            modal_dialog_add_creator = Layout()
            modal_dialog_add_contributor = Layout()
            modal_dialog_add_relation = Layout()
            modal_dialog_add_source = Layout()

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = "/hsapi/_internal/create-resource/"
        self.helper.form_tag = False

        layout = Layout(
                TabHolder(
                    Tab("Core Metadata",
                        HTML('<div class="form-group" id="title"> '
                                '{% load crispy_forms_tags %} '
                                '{% crispy title_form %} '
                                # '{% load inplace_edit %} '
                                # '{% for field in title_form %}'
                                # '{{ field.label_tag }} {% inplace_edit "field.field" %}'
                                #'{% inplace_edit "title_form.value" %} '
                                #'{% endfor %}'
                             '</div>'),

                        Accordion(
                            AccordionGroup('Keywords (required)',
                                 HTML('<div class="form-group" id="subjects"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy subjects_form %} '
                                      '</div>'),
                            ),
                            AccordionGroup('Abstract (required)',
                                 HTML('<div class="form-group" id="abstract"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy abstract_form %} '
                                      '</div>'),
                            ),
                            AccordionGroup('Rights (required)',
                                HTML('<div class="form-group" id="source"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy rights_form %} '
                                     '</div>'),
                            ),
                            AccordionGroup('Creators (required)',
                                HTML("<div class='form-group' id='creator'>"),
                                HTML("{{ creator_formset.management_form }}"),
                                creator_layout,
                                HTML("</div>"),
                            ),
                            AccordionGroup('Contributors (optional)',
                                HTML("<div class='form-group' id='contributor'>"),
                                HTML("{{ contributor_formset.management_form }}"),
                                contributor_layout,
                                HTML("</div>"),
                            ),
                            AccordionGroup('Relations (optional)',
                                HTML("<div class='form-group' id='relation'>"),
                                HTML("{{ relation_formset.management_form }}"),
                                relation_layout,
                                HTML("</div>"),
                            ),
                            AccordionGroup('Sources (optional)',
                                HTML("<div class='form-group' id='source'>"),
                                HTML("{{ source_formset.management_form }}"),
                                source_layout,
                                HTML("</div>"),
                            ),
                            AccordionGroup('Identifiers (required)',
                                HTML("<div class='form-group' id='identifier'>"),
                                HTML("{{ identifier_formset.management_form }}"),
                                identifier_layout,
                                HTML("</div>"),
                            ),

                            AccordionGroup('Language (optional)',
                                HTML('<div class="form-group" id="language"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy language_form %} '
                                     '</div>'),
                            ),
                            AccordionGroup('Valid date (optional)',
                                HTML('<div class="form-group" id="validdate"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy valid_date_form %} '
                                     '</div>'),
                            ),
                            AccordionGroup('Formats/MIME Types (optional)',
                                HTML("<div class='form-group' id='format'>"),
                                HTML("{{ format_formset.management_form }}"),
                                format_layout,
                                HTML("</div>"),
                            ),
                            AccordionGroup('Temporal Coverage (required)',
                                HTML('<div class="form-group" id="coverage-temporal"> '
                                         '{% load crispy_forms_tags %} '
                                         '{% crispy coverage_temporal_form %} '
                                     '</div>'),
                            ),
                            AccordionGroup('Spatial Coverage (required)',
                                HTML('<div class="form-group" id="coverage-spatial"> '
                                        '{% load crispy_forms_tags %} '
                                        '{% crispy coverage_spatial_form %} '
                                     '</div>'),
                            ),
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
        super(PartyForm, self).__init__(*args, **kwargs)
        self.profile_link_formset = None
        self.number = 0


    class Meta:
        model = Party
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage']

        # TODO: field labels and widgets types to be specified


class CreatorForm(PartyForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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


class PartyValidationForm(forms.Form):
    description = forms.URLField(required=False)
    name = forms.CharField(max_length=100)
    organization = forms.CharField(max_length=200, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=250, required=False)
    phone = forms.CharField(max_length=25, required=False)
    homepage = forms.URLField(required=False)


class CreatorValidationForm(PartyValidationForm):
    order = forms.IntegerField()


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

CreatorFormSet = formset_factory(CreatorForm, formset=BaseCreatorFormSet, extra=0)


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
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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


ContributorFormSet = formset_factory(ContributorForm, formset=BaseContributorFormSet)


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


class BaseRelationFormSet(BaseFormSet):
    def get_metadata(self):
        relations_data = []
        for form in self.forms:
            relation_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if len(relation_data) > 0:
                relations_data.append({'relation': relation_data})

        return relations_data


class RelationForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, *args, **kwargs):
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

        # TODO: field labels and widgets types to be specified


class RelationValidationForm(forms.Form):
    type = forms.CharField(max_length=100)
    value = forms.CharField(max_length=500)

RelationFormSet = formset_factory(RelationForm, formset=BaseRelationFormSet)

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


class BaseSourceFormSet(BaseFormSet):
    def get_metadata(self):
        sources_data = []
        for form in self.forms:
            source_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if len(source_data) > 0:
                sources_data.append({'source': source_data})

        return sources_data


class SourceForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, *args, **kwargs):
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


        # TODO: field labels and widgets types to be specified


class SourceValidationForm(forms.Form):
    derived_from = forms.CharField(max_length=300)


SourceFormSet = formset_factory(SourceForm, formset=BaseSourceFormSet)


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


class BaseIdentifierFormSet(BaseFormSet):
    def get_metadata(self):
        identifiers_data = []
        for form in self.forms:
            identifier_data = {k: v for k, v in form.cleaned_data.iteritems()}
            identifiers_data.append({'identifier': identifier_data})

        return identifiers_data


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

        # TODO: field labels and widgets types to be specified

IdentifierFormSet = formset_factory(IdentifierForm, formset=BaseIdentifierFormSet)


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


class BaseFormatFormSet(BaseFormSet):
    def get_metadata(self):
        formats_data = []
        for form in self.forms:
            format_data = {k: v for k, v in form.cleaned_data.iteritems()}
            formats_data.append({'format': format_data})

        return formats_data


class FormatForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, *args, **kwargs):
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

        # TODO: field labels and widgets types to be specified

FormatFormSet = formset_factory(FormatForm, formset=BaseFormatFormSet)


# Non repeatable element related forms
class BaseFormHelper(FormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None, element_layout=None,  *args, **kwargs):
        coverage_type = kwargs.pop('coverage', None)

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
            self.layout = Layout(
                            Fieldset(element_name,
                                     element_layout,
                            ),
                          )

class TitleFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('value', css_class=field_width),
                 )

        super(TitleFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class TitleForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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

    def get_metadata(self):
        return {'title': self.cleaned_data}

# This form handles multiple subject elements - this was not implemented as formset
# since we are providing one input field to enter multiple keywords (subjects) as comma separated values
class SubjectsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

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

    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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

    def get_metadata(self):
        return {'subject': self.cleaned_data}

class AbstractFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('abstract', css_class=field_width),
                 )

        super(AbstractFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class AbstractForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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

    def get_metadata(self):
        return {'description': self.cleaned_data}

class RightsFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('statement', css_class=field_width),
                        Field('url', css_class=field_width),
                 )

        super(RightsFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class RightsForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(RightsForm, self).__init__(*args, **kwargs)
        self.helper = RightsFormHelper(allow_edit, res_short_id, element_id, element_name='rights')

        if not allow_edit:
            for fld_name in self.Meta.fields:
                self.fields[fld_name].widget.attrs['readonly'] = True
                self.fields[fld_name].widget.attrs['style'] = "background-color:white;"

    class Meta:
        model = Rights
        fields = ['statement', 'url']
        exclude = ['content_object']


class RightsValidationForm(forms.Form):
    statement = forms.CharField(required=False)
    url = forms.URLField(required=False, max_length=500)

    def get_metadata(self):
        return {'rights': self.cleaned_data}


class CoverageTemporalFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('type', css_class=field_width),
                        Field('name', css_class=field_width),
                        Field('start', css_class=field_width),
                        Field('end', css_class=field_width),
                 )

        kwargs['coverage'] = 'temporal'

        super(CoverageTemporalFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class CoverageTemporalForm(forms.Form):
    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    start = forms.DateField(label='Start Date')
    end = forms.DateField(label='End Date')

    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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
        start_data = self.cleaned_data.get('start', None)
        end_data = self.cleaned_data.get('end', None)
        if not start_data:
            self._errors['start'] = ["Data for start date is missing"]
            is_form_errors = True

        if not end_data:
            self._errors['end'] = ["Data for end date is missing"]
            is_form_errors = True

        if is_form_errors:
            return self.cleaned_data

        if 'name' in self.cleaned_data:
            if len(self.cleaned_data['name']) == 0:
                del self.cleaned_data['name']

        self.cleaned_data['start'] = self.cleaned_data['start'].strftime('%m/%d/%Y')
        self.cleaned_data['end'] = self.cleaned_data['end'].strftime('%m/%d/%Y')
        self.cleaned_data['value'] = copy.deepcopy(self.cleaned_data)
        self.cleaned_data['type'] = 'period'
        if 'name' in self.cleaned_data:
            del self.cleaned_data['name']
        del self.cleaned_data['start']
        del self.cleaned_data['end']

        return self.cleaned_data

    def get_metadata(self):
        return {'coverage': self.cleaned_data}


class CoverageSpatialFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('type'),
                        Field('name', css_class=field_width),
                        Field('east', css_class=field_width),
                        Field('north', css_class=field_width),
                        Field('northlimit', css_class=field_width),
                        Field('eastlimit', css_class=field_width),
                        Field('southlimit', css_class=field_width),
                        Field('westlimit', css_class=field_width),
                        Field('units', css_class=field_width),
                        Field('uplimit', css_class=field_width),
                        Field('downlimit', css_class=field_width),
                        Field('elevation', css_class=field_width),
                        Field('zunits', css_class=field_width),
                        Field('projection', css_class=field_width),
                 )

        kwargs['coverage'] = 'spatial'
        super(CoverageSpatialFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)

class CoverageSpatialForm(forms.Form):
    TYPE_CHOICES = (
        ('box', 'Box'),
        ('point', 'Point')
    )
    #type = forms.CharField(max_length=20, widget=Select(choices=TYPE_CHOICES, attrs={'class': 'select'}))
    type = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.RadioSelect(renderer=HorizontalRadioRenderer))
    name = forms.CharField(max_length=200, required=False, label='Place/Area Name')
    east = forms.DecimalField()
    north = forms.DecimalField()
    units = forms.CharField(max_length=50)
    elevation = forms.DecimalField(required=False)
    zunits = forms.CharField(max_length=50, required=False)
    projection = forms.CharField(max_length=100, required=False)
    northlimit = forms.DecimalField(label='North Limit')
    eastlimit = forms.DecimalField(label='East Limit')
    southlimit = forms.DecimalField(label='South Limit')
    westlimit = forms.DecimalField(label='West Limit')
    uplimit = forms.DecimalField(required=False, label='Up Limit')
    downlimit = forms.DecimalField(required=False, label='Down Limit')

    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
        super(CoverageSpatialForm, self).__init__(*args, **kwargs)
        self.helper = CoverageSpatialFormHelper(allow_edit, res_short_id, element_id, element_name='coverage')
        self.number = 0
        self.delete_modal_form = None
        self.errors.clear()
        if res_short_id:
            self.action = "/hsapi/_internal/%s/coverage/add-metadata/" % res_short_id
        else:
            self.action = ""

        if not allow_edit:
            for field in self.fields.values():
                field.widget.attrs['readonly'] = True
                field.widget.attrs['style'] = "background-color:white;"

    #type = forms.CharField(max_length=20)
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

            if not east:
                self._errors['east'] = ["Data for east is missing"]
                is_form_errors = True

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
            if temp_cleaned_data['elevation'] is not None:
                temp_cleaned_data['elevation'] = str(temp_cleaned_data['elevation'])
            else:
                del temp_cleaned_data['zunits']
                del temp_cleaned_data['elevation']
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

            uplimit = temp_cleaned_data.get('uplimit', None)
            downlimit = temp_cleaned_data.get('downlimit', None)

            if uplimit and not downlimit:
                self._errors['downlimit'] = ["Data for downlimit is missing"]
                is_form_errors = True

            if downlimit and not uplimit:
                self._errors['uplimit'] = ["Data for uplimit is missing"]
                is_form_errors = True

            if is_form_errors:
                return self.cleaned_data

            temp_cleaned_data['northlimit'] = str(temp_cleaned_data['northlimit'])
            temp_cleaned_data['eastlimit'] = str(temp_cleaned_data['eastlimit'])
            temp_cleaned_data['southlimit'] = str(temp_cleaned_data['southlimit'])
            temp_cleaned_data['westlimit'] = str(temp_cleaned_data['westlimit'])
            if temp_cleaned_data['uplimit'] is not None:
                temp_cleaned_data['uplimit'] = str(temp_cleaned_data['uplimit'])
            else:
                del temp_cleaned_data['uplimit']

            if temp_cleaned_data['downlimit'] is not None:
                temp_cleaned_data['downlimit'] = str(temp_cleaned_data['downlimit'])
            else:
                del temp_cleaned_data['downlimit']

            if 'uplimit' not in temp_cleaned_data and 'downlimit' not in temp_cleaned_data:
                del temp_cleaned_data['zunits']

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

    def get_metadata(self):
        return {'coverage': self.cleaned_data}


class LanguageFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('code', css_class=field_width),
                 )

        super(LanguageFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class LanguageForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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

    def get_metadata(self):
        return {'language': self.cleaned_data}


class ValidDateFormHelper(BaseFormHelper):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, element_name=None,  *args, **kwargs):

        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        layout = Layout(
                        Field('start_date', css_class=field_width),
                        Field('end_date', css_class=field_width),
                 )

        super(ValidDateFormHelper, self).__init__(allow_edit, res_short_id, element_id, element_name, layout,  *args, **kwargs)


class ValidDateForm(ModelForm):
    def __init__(self, allow_edit=False, res_short_id=None, element_id=None, *args, **kwargs):
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
        labels = {'start_date': 'Start date', 'end_date': 'End date'}
        widgets = {'start_date': DateInput(), 'end_date': DateInput()}


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

    def get_metadata(self):
        if len(self.cleaned_data) > 0:
            self.cleaned_data['type'] = 'valid'
            return {'date': self.cleaned_data}
        else:
            return []