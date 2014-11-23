__author__ = 'pabitra'
from models import *
from django.forms import ModelForm
from django.forms.models import inlineformset_factory, modelformset_factory

class PartyForm(ModelForm):
    class Meta:
        #model = Party
        fields = ['description', 'name', 'organization', 'email', 'address', 'phone', 'homepage', 'researcherID', 'researcherGateID', 'external_links']

        # TODO: field labels and widgets types to be specified

ExternalProfileLinkFormSet = inlineformset_factory(Party, ExternalProfileLink)


class CreatorForm(PartyForm):
    class Meta(PartyForm.Meta):
        model = Creator
        super(CreatorForm).Meta.fields.append("order")

CreatorFormSet = modelformset_factory(Creator, CreatorForm)


class ContributorForm(PartyForm):
    class Meta(PartyForm.Meta):
        model = Contributor

ContributorFormSet = modelformset_factory(Contributor, ContributorForm)
