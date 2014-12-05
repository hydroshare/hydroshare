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
        #self.fields.keyOrder = ['name', 'description','organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']
        self.profile_link_formset = None
    class Meta:
        model = Party
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage']

        # TODO: field labels and widgets types to be specified

#ExternalProfileLinkFormSet = inlineformset_factory(Party, ExternalProfileLink)

class MetaDataForm(forms.Form):
    def __init__(self, extended_metadata_layout=None, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        if not extended_metadata_layout:
            extended_metadata_layout = Layout(HTML('<h3>No extended metadata for this resource.</h3>'))
        # self.layout = Layout(
        #     Fieldset('Creator', CreatorForm.Meta.fields),
        #     ButtonHolder(
        #         Submit('submit', 'Submit', css_class='button black')
        #     )
        # )
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
                         '<textarea class="mceEditor charfield" cols="40" id="" name="abstract" rows="10" placeholder="Abstract">"{{ abstract }}"</textarea>'
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
                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                 '<div class="item" '
                                 '{% crispy form %} '
                                 '{{ form.profile_link_formset.management_form }} '
                                 '{% for link_form in form.profile_link_formset.forms %} '
                                 '<div class="item_link" '
                                 '{% crispy link_form %} '
                                 '</div> {% endfor %} '
                                '<p><a id="addLinkCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another link</a></p>'
                                 '<p style="">'
                                 '<input class="delete-creator btn-danger btn btn-sm" type="button" value="Delete">'
                                 '</p>'
                                 '</div> {% endfor %}'),
                            HTML('<p><a id="addCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another creator</a></p>'),
                            HTML("</div>"),
                        ),
                        AccordionGroup('Contributors (optional)',
                            HTML("<div class='form-group' id='contributor'>"),
                            #HTML("<label for='' class='col-sm-2 control-label'>Contributors</label>"),
                            HTML("{{ contributor_formset.management_form }}"),
                            HTML('{% load crispy_forms_tags %} {% for form in contributor_formset.forms %} <div class="item" {% crispy form %} <p style=""><input class="delete-contributor btn-danger btn btn-sm" type="button" value="Delete"></p></div> {% endfor %}'),
                            HTML('<p><a id="addContributor" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another contributor</a></p>'),
                            #HTML("{{ contributor_formset }}"),
                            HTML("</div>")
                        )
                    ),
                ),

                # Specific resource type app needs to provide the crispy form Layout object: extended_metadata_layout
                Tab("Extended Metadata",
                    extended_metadata_layout,
                    # HTML('{% if extended_metadata_layout %} '
                    #      '<h3>No extended metadata available for this resource.</h3> '
                    #      '{% endif %}'
                    # ),
                )
            )
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
    def __init__(self, *args, **kwargs):
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()

    class Meta:
        model = Creator
        fields = PartyForm.Meta.fields
        fields.append("order")
        #labels = PartyForm.Meta.labels

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

CreatorFormSet = formset_factory(CreatorForm, extra=0, formset=BaseCreatorFormSet, can_order=True)

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
