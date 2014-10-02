__author__ = 'valentin'
#from mezzanine.forms.models import Form
from django.forms import ModelForm, Textarea
from django import forms
from django.forms.models import inlineformset_factory,modelformset_factory,BaseModelFormSet

from ..models.organization import Organization
from ..models.person import Person,PersonLocation,PersonExternalIdentifier,\
    PersonPhone,PersonEmail,OtherName
from ..models.organization_association import OrganizationAssociation
from .organization_association import OrganizationAssociationEditorForm

from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import TabHolder, Tab
class PersonCreateForm(ModelForm):


    class Meta:
        model = Person
        fields = ( 'name','givenName','familyName','primaryOrganizationRecord',
                   'jobTitle','notes','url',
        #           'primaryAddress',"primaryTelephone"
        )
        widgets = {
            'notes': Textarea(attrs={'cols': 80, 'rows': 6}),
        }
        labels = {
            'notes': _('Short Bio'),
            'name': _('Full Name of Person (must be unique)'),
            'primaryOrganizationRecord': _('Select Primary Organization'),
            'givenName': _('First or Given Name'),
            'familyName': _('Last or Family Name'),
        }
        help_texts = {
            'notes': _('Short Biography discussing you work and interests.'),
            'name': _('Full Name of Person that will be displayed on the site. Must be unique.'),
        }


# intial form
class PersonEditorForm(ModelForm):


    class Meta:
        model = Person
        fields = ( 'name','givenName','familyName','primaryOrganizationRecord',
                   'jobTitle','notes','url',
        #           'primaryAddress',"primaryTelephone"
        )
        widgets = {
            'notes': Textarea(attrs={'cols': 80, 'rows': 6}),
        }
        labels = {
            'notes': _('Short Bio'),
            'name': _('Full Name of Person (must be unique)'),
            'primaryOrganizationRecord': _('Select Primary Organization'),
        }
        help_texts = {
            'notes': _('Short Biography discussing you work and interests.'),
            'name': _('Full Name of Person that will be displayed on the site. Must be unique.'),
        }


    pass

LocationFormSet = inlineformset_factory(
    Person,
    PersonLocation,
    extra=2,)
EmailFormSet = inlineformset_factory(
    Person,
    PersonEmail,
    extra=2,)
PhoneFormSet = inlineformset_factory(
    Person,
    PersonPhone,
    extra=2,)
NameFormSet = inlineformset_factory(
    Person,
    OtherName,
    extra=2,)
IdentifierFormSet = inlineformset_factory(
    Person,
    PersonExternalIdentifier,
    extra=2,)

OrgAssociationsFormSet = inlineformset_factory(
    Person,
    Organization.persons.through,
    #Person.organizations.through,
    extra=2)

# class OrganizationAssociationFormset(BaseModelFormSet):
#     def __init__(self, *args, **kwargs):
#         super(OrganizationAssociationFormset, self).__init__(*args, **kwargs)
#         self.queryset = OrganizationAssociation.objects.filter(name__startswith='O')

# OrgAssociationsFormSet = modelformset_factory(
#     OrganizationAssociation,
# #    form=OrganizationAssociationEditorForm,
#     extra=2)

# class PersonForm(ModelForm):
#     class Meta:
#         model = Person
#         fields ={"givenName","familyName","name",}
#
#     pass