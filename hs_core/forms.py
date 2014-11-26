from django.utils.datastructures import SortedDict

__author__ = 'pabitra'
from models import *
from django.forms import ModelForm
from django.forms.models import inlineformset_factory, modelformset_factory, formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, HTML
from crispy_forms.bootstrap import *

class PartyForm(ModelForm):
    # def __init__(self, *args, **kwargs):
    #     super(PartyForm, self).__init__(*args, **kwargs)
    #     self.fields.keyOrder = ['name', 'description','organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']
    class Meta:
        model = Party
        # TODO: Not sure why the fields are not displayed in the order specified here
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']


        # TODO: field labels and widgets types to be specified

#ExternalProfileLinkFormSet = inlineformset_factory(Party, ExternalProfileLink)

class MetaDataForm(forms.Form):
    def __init__(self, extended_metadata_layout=None, *args, **kwargs):
        super(MetaDataForm, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        # self.layout = Layout(
        #     Fieldset('Creator', CreatorForm.Meta.fields),
        #     ButtonHolder(
        #         Submit('submit', 'Submit', css_class='button black')
        #     )
        # )
        self.helper = FormHelper()
        self.helper.layout = Layout(
            TabHolder(
                Tab("Core Metadata",
                    #HTML("{% load crispy_forms_tags %}"),

                    Accordion(
                        AccordionGroup('*Creators',
                            HTML("<div class='form-group'>"),
                            HTML("<label for='' class='col-sm-2 control-label'></label><br>"),

                            HTML("{{ creator_formset.management_form }}"),

                            HTML('{% load crispy_forms_tags %} '
                                 '{% for form in creator_formset.forms %} '
                                 '<div class="item" '
                                 '{% crispy form %} '
                                 '<p style="">'
                                 '<input class="delete-creator btn-danger btn btn-sm" type="button" value="Delete">'
                                 '</p>'
                                 '</div> {% endfor %}'),
                            HTML('<p><a id="addCreator" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another creator</a></p>'),
                            # HTML("{{ form }}"),
                            # HTML('<p style=""><a class="delete" href="#">Delete</a></p>'),
                            # HTML("{% endfor %}"),
                            #HTML("{{ creator_formset }}"),

                            HTML("</div>"),
                        ),
                        AccordionGroup('Contributors',
                            HTML("<div class='form-group'>"),
                            #HTML("<label for='' class='col-sm-2 control-label'>Contributors</label>"),
                            HTML("{{ contributor_formset.management_form }}"),
                            HTML('{% load crispy_forms_tags %} {% for form in contributor_formset.forms %} <div class="item" {% crispy form %} <p style=""><input class="delete-contributor btn-danger btn btn-sm" type="button" value="Delete"></p></div> {% endfor %}'),
                            HTML('<p><a id="addContributor" class="btn btn-success" href="#"><i class="fa fa-plus"></i>Add another contributor</a></p>'),
                            #HTML("{{ contributor_formset }}"),
                            HTML("</div>")
                        )
                    ),
                ),

                # Specific resource type app needs provide the crispy form Layout object: extended_metadata_layout
                Tab("Extended Metadata",
                    extended_metadata_layout,
                    HTML('{% if not extended_metadata_layout %} <h3>No extended metadata available for this resource.</h3> {% endif %}'),
                )
            )
        )

class CreatorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(CreatorFormSetHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        self.layout = Layout(
            Fieldset('Creator', CreatorForm.Meta.fields),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button black')
            )
        )
        # self.layout = Layout(
        #     TabHolder(
        #         Tab("Core Metadata", CreatorForm.Meta.fields)
        #     )
        # )
        #self.render_required_fields = True,


class CreatorForm(PartyForm):
    def __init__(self, *args, **kwargs):
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()
        # self.helper.layout = Layout(
        #     Fieldset('Creator', 'item-1', 'item-2'),
        #     ButtonHolder(
        #         Submit('submit', 'Submit', css_class='button black')
        #     )
        # )
    class Meta:
        model = Creator
        fields = PartyForm.Meta.fields
        #fields.append("order")

CreatorFormSet = formset_factory(CreatorForm)

class ContributorFormSetHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(ContributorFormSetHelper, self).__init__(*args, **kwargs)
        #self.form_method = 'post'
        self.layout = Layout(
            Fieldset('Contributor', ContributorForm.Meta.fields.keyOrder),
            ButtonHolder(
                Submit('submit', 'Submit', css_class='button black')
            )
        )
        # self.layout = Layout(
        #     TabHolder(
        #         Tab("Core Metadata", CreatorForm.Meta.fields)
        #     )
        # )
        self.render_required_fields = True,

class ContributorForm(PartyForm):
    def __init__(self, *args, **kwargs):
        super(ContributorForm, self).__init__(*args, **kwargs)
        self.helper = ContributorFormSetHelper()

    class Meta:
        model = Contributor
        fields = PartyForm.Meta.fields
        #fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']
        # if 'order' in fields:
        #     fields.remove('order')

ContributorFormSet = formset_factory(ContributorForm)
