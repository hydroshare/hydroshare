from __future__ import absolute_import
from django.test import TestCase
from django.contrib.auth import get_user_model
#from django_webtest import WebTest
from ..models.organization import Organization,OrganizationCodeList,ExternalOrgIdentifier
from ..models.person import    Person
from ..models.organization_association import OrganizationAssociation
from ..models.party_types import  ExternalIdentifierCodeList
from ..models.party import Party

from datetime import date

from .test_person import AddPeople
from .test_organization import createOrgBasic

# goal show that retrieving a party, retrieves orgs and persons
class PartyTest(TestCase):

    def setUp(self):
        AddPeople()
        createOrgBasic()

    def test_fetchparty(self):
        personcount = Person.objects.all().count()
        orgcount = Organization.objects.all().count()

        parties = Party.objects.all()

        self.assertEqual(parties.count(), personcount + orgcount)




