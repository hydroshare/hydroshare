from __future__ import absolute_import
from django.test import TestCase
from django.utils.unittest import skipUnless
from django.core.urlresolvers import reverse,resolve,reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User,Group
#from django_webtest import WebTest
from ..models.organization import Organization,OrganizationCodeList
from ..models.person import Person
from ..models.organization_association import  OrganizationAssociation

from datetime import date
from django.test.utils import override_settings

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from mezzanine.conf import settings

__author__ = 'valentin'


class UserOrgViewTests(TestCase):
    fixtures =['initial_data.json']
    # should be able to do this, but
    # issue: need to override base page or you see this error
    #  NoReverseMatch: Reverse for 'blog_post_feed'
    #urls = 'hs_scholar_profile.urls'

    def setUp(self):
        otherChoice = OrganizationCodeList.objects.get(code='other')
        self.aPerson = Person.objects.create(givenName="last", familyName="first", name="last first")
        self.org2 = Organization.objects.create(name="org2",organizationType=otherChoice)
        self.oa1 = OrganizationAssociation.objects.create(person=self.aPerson,organization=self.org2)



    @override_settings(TEST_RUNNER = 'django.test.simple.DjangoTestSuiteRunner')
    def test_person_list_view(self):
        plist = reverse("person_list")
        response = self.client.get(plist)
        self.assertEqual(response.status_code, 200)

    def test_person_create(self):
        response = self.client.get(reverse("person_add" ) )
        self.assertEqual(response.status_code, 200)



    def test_organization_list_view(self):
        response = self.client.get(reverse("organization_list"))
        self.assertEqual(response.status_code, 200)


    def test_person_detail_view(self):
        response = self.client.get(reverse("person_detail", args=[ self.aPerson.id] ) )
        self.assertEqual(response.status_code, 200)

    def test_organization_detail_view(self):
        response = self.client.get(reverse("organization_detail", args=[  self.org2.id] ) )
        self.assertEqual(response.status_code, 200)


    def test_organization_create(self):
        response = self.client.get(reverse("organization_add" ) )
        self.assertEqual(response.status_code, 200)


    def test_association_create(self):
        response = self.client.get(reverse("association_add" ) )
        self.assertEqual(response.status_code, 200)


    def test_association_edit(self):
        response = self.client.get(reverse("association_edit" , args=['1']) )
        self.assertEqual(response.status_code, 200)



# tried:  resolve....)
    # people, /people, /people/
    # party/people, /party/people
    # hs_user_org:people
    # def test_urls(self):
    #     response = self.client.get(resolve('hs_user_org:people'))
    #     self.assertEqual(response.status_code, 200)
