from django.utils.datastructures import SortedDict

__author__ = 'pabitra'
from models import *
from django.forms import ModelForm, BaseFormSet
from django.forms.models import inlineformset_factory, modelformset_factory, formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.bootstrap import *
from django.utils.translation import ugettext_lazy as _

class PartyForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PartyForm, self).__init__(*args, **kwargs)
        self.profile_link_formset = None

    class Meta:
        model = Party
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage']

        # TODO: field labels and widgets types to be specified

#ExternalProfileLinkFormSet = inlineformset_factory(Party, ExternalProfileLink)
ModalDialogLayout = Layout(
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
                                                    '{% for link_form in add_creator_modal_form.profile_link_formset.forms %} '
                                                     '<div class="item_link" '
                                                     '{% crispy link_form %} '
                                                     '</div> {% endfor %} '
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

ModalConfirmDeleteMetaDataElement = Layout(
                                            HTML('<div class="modal fade" id="delete-metadata-element-dialog" tabindex="-1" role="dialog" aria-labelledby="myModalLabel" aria-hidden="true">'
                                                    '<div class="modal-dialog">'
                                                        '<div class="modal-content">'),
                                                            HTML('<form action="{{ form.delete_modal_form.element_delete_action }}" > '),
                                                            HTML('<div class="modal-header">'
                                                                '<button type="button" class="close" data-dismiss="modal" aria-hidden="true">&times;</button>'
                                                                '<h4 class="modal-title" id="myModalLabel">Delete metadata element</h4>'
                                                            '</div>'
                                                            '<div class="modal-body">'
                                                                '<strong>Are you sure you want to delete this metadata element?</strong>'

                                                            '</div>'
                                                            '<div class="modal-footer">'
                                                                '<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>'
                                                                '<button type="submit" class="btn btn-danger">Delete</button>'
                                                            '</div>'
                                                            '</form>'
                                                        '</div>'
                                                    '</div>'
                                                '</div>'),
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

CreatorLayoutEdit = Layout(
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                     '<div class="item form-group"> '
                                     '<form action="{{ form.action }}" method="POST" enctype="multipart/form-data"> '
                                     '{% crispy form %} '
                                        '{{ form.profile_link_formset.management_form }} '
                                        '{% for link_form in form.profile_link_formset.forms %} '
                                            '<div class="item_link"> '
                                                '{% crispy link_form %} '
                                            '</div>'
                                        '{% endfor %} '
                                    '<div style="margin-top:10px"><a id="addLinkCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another link</a></div>'
                                     #'<p style="">'
                                    '<div class="row" style="margin-top:10px">'
                                        '<div class="col-md-10">'
                                            '<input class="btn-danger btn btn-md" type="button" data-toggle="modal" data-target="#delete-metadata-element-dialog" value="Delete creator">'
                                        '</div>'
                                        '<div class="col-md-2">'
                                            '<button type="submit" class="btn btn-primary">Save Changes</button>'
                                        '</div>'
                                    '</div>'
                                    '{% crispy form.delete_modal_form %} '
                                    #'</p>'
                                    '</div> '
                                    '</form> '
                                '{% endfor %}'
                            ),
                            HTML('<div style="margin-top:10px"><p><a id="add-creator" class="btn btn-success" data-toggle="modal" data-target="#add-creator-dialog"><i class="fa fa-plus"></i>Add another creator</a></div>'),
                            HTML("</div>"),

)

class MetaDataElementDeleteForm(forms.Form):
    def __init__(self, res_short_id, element_name, element_id , *args, **kwargs):
        super(MetaDataElementDeleteForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.delete_element_action = "/hsapi/_internal/%s/%s/%s/delete-metadata/" % (res_short_id, element_name, element_id)
        self.helper.layout = ModalConfirmDeleteMetaDataElement
        self.helper.layout[1] = HTML('<form action=%s>' % self.delete_element_action)
        self.helper.form_tag = False

class MetaDataForm(forms.Form):
    def __init__(self, resource_mode='new', extended_metadata_layout=None, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        if not extended_metadata_layout:
            extended_metadata_layout = HTML('<h3>No extended metadata for this resource.</h3>')
        # self.layout = Layout(
        #     Fieldset('Creator', CreatorForm.Meta.fields),
        #     ButtonHolder(
        #         Submit('submit', 'Submit', css_class='button black')
        #     )
        # )
        if resource_mode == 'new':
            creator_layout = CreatorLayoutNew
            modal_dialog_layout = Layout()
        else:
            creator_layout = CreatorLayoutEdit
            modal_dialog_layout = ModalDialogLayout

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = "/hsapi/_internal/create-resource/"
        self.helper.form_tag = False
        self.helper.layout = Layout(
            TabHolder(
                Tab("Core Metadata",
                    HTML('<div class="form-group">'
                         '<label for="" control-label">Title</label>'
                         '<input type="text" class="form-control input-sm" name="title" id="" placeholder="Title" value="{{ title }}">'
                         '</div>'),

                    HTML('<div class="form-group">'
                         '<label for="" control-label">Abstract</label>'
                         '<textarea class="mceEditor charfield" cols="40" id="" name="abstract" rows="10" placeholder="Abstract">{{ abstract }}</textarea>'
                         '</div>'),

                    HTML('<div class="form-group">'
                         '<label for="" control-label">Keywords</label>'
                         '<input type="text" class="form-control" id="" name="keywords" placeholder="Keywords">'
                         '</div>'),
                    Accordion(
                        AccordionGroup('Creators (required)',
                            HTML("<div class='form-group' id='creator'>"),

                            #HTML("<label for='' class='col-sm-2 control-label'></label><br>"),

                            HTML("{{ creator_formset.management_form }}"),

                            #HTML("{{ creator_profilelink_formset.management_form }}"),
                            creator_layout,
                            # HTML('{% load crispy_forms_tags %} '
                            #      '{% for form in creator_formset.forms %} '
                            #      '<div class="item" '
                            #      '{% crispy form %} '
                            #      '{{ form.profile_link_formset.management_form }} '
                            #      '{% for link_form in form.profile_link_formset.forms %} '
                            #      '<div class="item_link" '
                            #      '{% crispy link_form %} '
                            #      '</div> {% endfor %} '
                            #     '<p><a id="addLinkCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another link</a></p>'
                            #      '<p style="">'
                            #      '<input class="delete-creator btn-danger btn btn-sm" type="button" value="Delete creator">'
                            #      '</p>'
                            #      '</div> {% endfor %}'),
                            # HTML('<p><a id="addCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another creator</a></p>'),
                            HTML("</div>"),
                        ),
                        AccordionGroup('Contributors (optional)',
                            HTML("<div class='form-group' id='contributor'>"),
                                HTML("{{ contributor_formset.management_form }}"),
                                HTML('{% load crispy_forms_tags %} '
                                     '{% for form in contributor_formset.forms %} '
                                     '<div class="item"> '
                                        '{% crispy form %} '
                                        '<input class="delete-contributor btn-danger btn btn-md" type="button" style="margin-top:10px" value="Delete contributor">'
                                     '</div> '
                                     '{% endfor %}'),
                                HTML('<p><a id="addContributor" class="btn btn-success" style="margin-top:10px" href="#"><i class="fa fa-plus"></i>Add another contributor</a></p>'),
                            HTML("</div>")
                        )
                    ),
                ),

                # Specific resource type app needs to provide the crispy form Layout object: extended_metadata_layout
                Tab("Extended Metadata",
                    extended_metadata_layout,
                ),
            ),
            modal_dialog_layout,
        )

class ProfileLinksFormSetHelper(FormHelper):
    def __init__(self, link_for, *args, **kwargs):
        super(ProfileLinksFormSetHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
        if link_for == 'creator':
            delete_btn_class = 'btn-danger delete-link-creator'
        else:
            delete_btn_class = 'btn-danger delete-link-contributor'

        self.layout = Layout(
            Fieldset('External Profile Link',
                     Field('type', css_class=field_width),
                     Field('url', css_class=field_width),
                     HTML('<div style="margin-top:10px"></div>')
                     ),
            ButtonHolder(
                #StrictButton('Add Link', css_class='btn-success'),
                StrictButton('Delete Link', css_class=delete_btn_class),
            )
        )

class ProfileLinksForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ProfileLinksForm, self).__init__(*args, **kwargs)
        self.helper = ProfileLinksFormSetHelper(link_for='creator')

    class Meta:
        model = ExternalProfileLink
        fields = ['type', 'url']


class BaseProfileLinkFormSet(BaseFormSet):
    def get_metadata_dict(self):
        links_data = []
        for form in self.forms:
            link_data = {k: v for k, v in form.cleaned_data.iteritems()}
            links_data.append(link_data)

        return {'profile_links': links_data}

ProfileLinksFormset = formset_factory(ProfileLinksForm, formset=BaseProfileLinkFormSet)

class CreatorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(CreatorFormSetHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # the order in which the model fields are listed for the FieldSet is the order these fields will be displayed
        field_width = 'form-control input-sm'
        self.form_tag = False
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


class CreatorForm(PartyForm):
    def __init__(self, res_short_id=None, element_id=None, *args, **kwargs):
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()
        self.profile_link_formset = ProfileLinksFormset(prefix='creator_links')
        self.delete_modal_form = None
        if res_short_id:
            # self.helper.form_method = 'post'
            # self.helper.form_tag = True
            # if len(self.initial) > 0:
            #     self.action = "/hsapi/_internal/%s/creator/%s/update-metadata/" % (res_short_id, self.initial['id'])
            #     pass
            # else:
            self.action = "/hsapi/_internal/%s/creator/add-metadata/" % res_short_id
        else:
            self.action = ""

    class Meta:
        model = Creator
        fields = PartyForm.Meta.fields
        fields.append("order")
        #labels = PartyForm.Meta.labels


class CreatorValidationForm(forms.Form):
    description = forms.URLField(required=False)
    name = forms.CharField(max_length=100)
    organization = forms.CharField(max_length=200, required=False)
    email = forms.EmailField(required=False)
    address = forms.CharField(max_length=250, required=False)
    phone = forms.CharField(max_length=25, required=False)
    homepage = forms.URLField(required=False)
    order = forms.IntegerField()



class BaseCreatorFormSet(BaseFormSet):
    def add_fields(self, form, index):
        super(BaseCreatorFormSet, self).add_fields(form, index)

        # create the nested profile link formset
        form.profile_link_formset = ProfileLinksFormset(prefix='creator_links-%s' % index)

    def get_metadata_dict(self):
        creators_data = []
        for form in self.forms:
            creator_data = {k: v for k, v in form.cleaned_data.iteritems()}
            if form.profile_link_formset.is_valid():
                profile_link_dict = form.profile_link_formset.get_metadata_dict()
                if len(profile_link_dict['profile_links']) > 0:
                    creator_data['profile_links'] = profile_link_dict['profile_links']

            creators_data.append({'creator': creator_data})

        return creators_data

CreatorFormSet = formset_factory(CreatorForm, formset=BaseCreatorFormSet, extra=0)

#CreatorExternalProfileLinkFormSet = inlineformset_factory(Creator, ExternalProfileLink)

class ContributorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ContributorFormSetHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
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
            # ButtonHolder(
            #     Submit('button', 'Save', css_class='button black')
            #)
        )

        self.render_required_fields = True,


class ContributorForm(PartyForm):
    def __init__(self, *args, **kwargs):
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.helper = ContributorFormSetHelper()

    class Meta:
        model = Contributor
        fields = PartyForm.Meta.fields
        if 'order' in fields:
            fields.remove('order')
        #labels = PartyForm.Meta.labels

class BaseContributorFormSet(BaseFormSet):
    def get_metadata_dict(self):
        for form in self.forms:
            contributor_data = {k: v for k, v in form.cleaned_data.iteritems()}
        return {'contributor': contributor_data}

ContributorFormSet = formset_factory(ContributorForm, formset=BaseContributorFormSet)
