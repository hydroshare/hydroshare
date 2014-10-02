__author__ = 'valentin'
#from mezzanine.forms.models import Form
from django.forms import ModelForm, Textarea
from django import forms
from django.forms.models import inlineformset_factory

from ..models.organization import Organization
from ..models.person import Person
from ..models.organization_association import OrganizationAssociation

from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _


# intial form
class OrganizationAssociationEditorForm(ModelForm):

    class Meta:
        model = OrganizationAssociation
        fields = ["person","organization","jobTitle","beginDate",
              "endDate","presentOrganization",]
        # widgets = {
        #     'jobTitle': Textarea(attrs={'cols': 80, 'rows': 6}),
        # }
        labels = {
            'jobTitle': _('Title of position in organization, if known'),
        }

    pass