from __future__ import absolute_import
from django.test import TestCase
from django.contrib.auth import get_user_model
#from django_webtest import WebTest
from ..models.organization import Organization,OrganizationCodeList,ExternalOrgIdentifier,\
    OrganizationLocation,OrganizationPhone,OrganizationEmail
from ..models.person import    Person
from ..models.organization_association import OrganizationAssociation
from ..models.party_types import  ExternalIdentifierCodeList,AddressCodeList,PhoneCodeList,EmailCodeList
from datetime import date



__author__ = 'valentin'


def createOrgBasic():
        otherChoice = OrganizationCodeList.objects.get(code='other')
        anOrg = Organization.objects.create(name="org1",organizationType=otherChoice)
        return anOrg

class organizationTest(TestCase):
    fixtures =['initial_data.json']

    def setUp(self):
        otherChoice = OrganizationCodeList.objects.get(code='other')
        idChoice = ExternalIdentifierCodeList.objects.get(code='other')
        self.p1 = Person.objects.create(givenName="first", familyName="last", name="First Last")
        self.p2 = Person.objects.create(givenName="last", familyName="first", name="last first")
        Organization.objects.create(name="org1",organizationType=otherChoice)
        self.org2 = Organization.objects.create(name="org2",organizationType=otherChoice)
        OrganizationAssociation.objects.create(person=self.p1,organization=self.org2,beginDate=date(2013,01,01))
        OrganizationAssociation.objects.create(person=self.p2,organization=self.org2,beginDate=date(2014,01,01))
        self.org3 = Organization.objects.create(name="org3",organizationType=otherChoice)
        OrganizationAssociation.objects.create(person=self.p1,organization=self.org3,beginDate=date(2013,01,10), endDate=date(2013,02,01), presentOrganization=False)
        OrganizationAssociation.objects.create(person=self.p2,organization=self.org3,beginDate=date(2014,01,01))
        ExternalOrgIdentifier.objects.create(organization=self.org2,identifierName=idChoice,identifierCode="code1")
        self.org3.parentOrganization = self.org2
        self.org3.save()



    def test_organization(self):

        org1 = Organization.objects.get(name="org1")
        self.assertEqual(org1.persons.count(), 0)
        org2 = Organization.objects.get(name="org2")
        self.assertEqual(org2.persons.count(), 2)
        associations = OrganizationAssociation(presentOrganization=True,organization=org2)
        self.assertEqual(associations.presentOrganization, True)
        self.assertEqual(associations.organization, org2)

        org3 = Organization.objects.get(name="org3")
        self.assertEqual(org3.persons.count(), 2)
        # need to learn the query languages and query set
        #self.assertEqual(org3..get(presentOrganization=True), 1)

    def test_association(self):
        # need to find a way to get association to test begin data time
        # self.assertEqual(org3.persons.get(familyName='last')., 1)
        p1 = Person.objects.get(familyName="last")
        print(p1.familyName)
        print(p1.organizations.count())
        #print(p.name for p in  p1.organizations)
        self.assertEqual(p1.organizations.count(), 2)
        pass

    def test_association_filter(self):
        # confused... should this be organizations like the related_name= field
        allorg = Person.objects.filter(organizationassociation__presentOrganization=False )
        print(allorg.count())
        self.assertEqual(allorg.count(),1)
        self.assertEquals(self.p1.pk, allorg.first().pk)

        p1org = Person.objects.filter(familyName__exact='last',organizationassociation__presentOrganization=True )
        self.assertEqual(p1org.count(),1)
        pass

    def test_externalIdentifier(self):
        org2 = Organization.objects.get(name="org2")
        self.assertEqual(org2.externalIdentifiers.count(), 1)

    def test_parent(self):
        org2 =  Organization.objects.get(name="org2")
        org3 = Organization.objects.get(name="org3")
        self.assertEqual(org3.parentOrganization, org2)

    def test_businessAddress_get(self):
        org1 = Organization.objects.get(name="Default Organization")

        addr = OrganizationLocation.objects.filter(organization=org1,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, org1.businessAddress)


    def test_businessAddress_set(self):
        org1 = Organization.objects.get(name="Default Organization")
        ADDRESS = "setNewAddress"
        org1.businessAddress = ADDRESS
        self.assertEqual(ADDRESS, org1.businessAddress)

        addr = OrganizationLocation.objects.filter(organization=org1,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, org1.businessAddress)

    def test_businessAddress_addnew(self):
        self.assertIsNotNone(self.org2)
        self.assertFalse(self.org2.businessAddress)
        ADDRESS = "setNewAddress"
        address_type = AddressCodeList.objects.get(code='primary')
        self.org2.businessAddress = ADDRESS
        self.assertEqual(ADDRESS, self.org2.businessAddress)

        addr = OrganizationLocation.objects.filter(organization=self.org2,address_type__code='primary')
        self.assertEqual(addr.count(),1)
        self.assertEqual(addr.first().address, self.org2.businessAddress)


    def test_businessTelephone_addnew(self):
        self.assertIsNotNone(self.org2)
        self.assertFalse(self.org2.businessTelephone)
        ADDRESS = "setNewAddress"
        address_type = PhoneCodeList.objects.get(code='primary')
        self.org2.businessTelephone = ADDRESS
        self.assertEqual(ADDRESS, self.org2.businessTelephone)

        phones = OrganizationPhone.objects.filter(organization=self.org2,phone_type__code='primary')
        self.assertEqual(phones.count(),1)
        self.assertEqual(phones.first().phone_number, self.org2.businessTelephone)

    def test_businessEmail_addnew(self):
        self.assertIsNotNone(self.org2)
        self.assertFalse(self.org2.businessEmail)
        ADDRESS = "me@example.com"
        address_type = EmailCodeList.objects.get(code='primary')
        self.org2.businessEmail = ADDRESS
        self.assertEqual(ADDRESS, self.org2.businessEmail)

        phones = OrganizationEmail.objects.filter(organization=self.org2,email_type__code='primary')
        self.assertEqual(phones.count(),1)
        self.assertEqual(phones.first().email, self.org2.businessEmail)
    pass