from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models.organization import ExternalOrgIdentifier
from ..models.party_types import ExternalIdentifierCodeList
from ..models.organization import Organization,OrganizationCodeList

__author__ = 'valentin'


class testExternalOrgIdentifiers(TestCase):
    fixtures =['initial_data.json']

    def setUp(self):
        self.idName = ExternalIdentifierCodeList.objects.get(code='other')
        idName2 = ExternalIdentifierCodeList.objects.get(code='twitter')
        self.orgType = OrganizationCodeList.objects.get(code="other")
        self.orgname = 'org1'
        self.identifierCode = "testExternalOrg"
        self.org = Organization.objects.create(name=self.orgname, organizationType = self.orgType)
        ExternalOrgIdentifier.objects.create(identifierCode = self.identifierCode,
              identifierName = self.idName, organization = self.org)

        ExternalOrgIdentifier.objects.create(identifierCode = "testExternalOrg2",
       identifierName = idName2, organization = self.org
        )


    def test_ExternalOrgIdentifiers(self):
        """just a quick test to learn testing"""
        extorg1 = ExternalOrgIdentifier.objects.get(identifierCode=self.identifierCode)
        self.assertEqual(extorg1.organization.name, self.org.name)
        self.assertEqual(extorg1.identifierCode, self.identifierCode)
        self.assertIsNotNone(extorg1.createdDate)






