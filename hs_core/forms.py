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
    # def __init__(self, *args, **kwargs):
    #     super(PartyForm, self).__init__(*args, **kwargs)
    #     self.fields.keyOrder = ['name', 'description','organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']
    class Meta:
        model = Party
        # fields that will be displayed are specified here - but not necessarily in the same order
        fields = ['name', 'description', 'organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researchGateID']

        labels = {
            'researcherID': _('Researcher ID'),
            'researchGateID': _('Research Gate ID')
        }
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
        self.helper.form_method = 'post'
        self.helper.form_action = "/hsapi/_internal/create-resource/"
        self.helper.form_tag = False
        self.helper.layout = Layout(
            TabHolder(
                Tab("Core Metadata",
                    #HTML("{% load crispy_forms_tags %}"),
                    HTML('<div class="form-group">'
                         '<label for="" control-label">Title</label>'
                         '<input type="text" class="form-control input-sm" name="title" id="" placeholder="Title">'
                         '</div>'),

                    HTML('<div class="form-group">'
                         '<label for="" control-label">Abstract</label>'
                         '<textarea class="mceEditor charfield" cols="40" id="" name="abstract" rows="10" placeholder="Abstract"> </textarea>'
                         '</div>'),

                    HTML('<div class="form-group">'
                         '<label for="" control-label">Keywords</label>'
                         '<input type="text" class="form-control" id="" name="keywords" placeholder="Keywords">'
                         '</div>'),
                    Accordion(
                        AccordionGroup('Creators (required)',
                            HTML("<div class='form-group' id='creators'>"),
                            #HTML("<label for='' class='col-sm-2 control-label'></label><br>"),

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
                        AccordionGroup('Contributors (optional)',
                            HTML("<div class='form-group' id='contributors'>"),
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
                     Field('researcherID', css_class=field_width),
                     Field('researchGateID', css_class=field_width),
                     Field('order', css_class=field_width),
                     ),
            # ButtonHolder(
            #     Submit('button', 'Save', css_class='button black')
            # )
        )


class CreatorForm(PartyForm):
    def __init__(self, *args, **kwargs):
        super(CreatorForm, self).__init__(*args, **kwargs)
        self.helper = CreatorFormSetHelper()

    class Meta:
        model = Creator
        fields = PartyForm.Meta.fields
        fields.append("order")
        labels = PartyForm.Meta.labels

class BaseCreatorFormSet(BaseFormSet):
    def get_metadata_dict(self):
        for form in self.forms:
            creator_data = {k: v for k, v in form.cleaned_data.iteritems()}
        return {'creator': creator_data}

CreatorFormSet = formset_factory(CreatorForm, extra=0, formset=BaseCreatorFormSet)


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
                     Field('researcherID', css_class=field_width),
                     Field('researchGateID', css_class=field_width),
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
        labels = PartyForm.Meta.labels

ContributorFormSet = formset_factory(ContributorForm)
