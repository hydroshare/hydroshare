from __future__ import absolute_import
from django.test import TestCase
from django.utils.unittest import skipUnless
from django.core.urlresolvers import reverse,resolve,reverse_lazy
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User,Group
#from django_webtest import WebTest
from django.http import HttpRequest

from ..models.organization import Organization,OrganizationCodeList
from ..models.person import Person
from ..models.organization_association import  OrganizationAssociation


from ..api import PersonResource,OrganizationResource,OrganizationAssociationResource

from datetime import date
from django.test.utils import override_settings
from tastypie.test import ResourceTestCase

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

from mezzanine.conf import settings

__author__ = 'valentin'


class PartyApiTests(ResourceTestCase):
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


    # def test_coreapi_api(self):
    #     plist = reverse('api_dispatch_list', kwargs={'resource_name': 'genericresource','api_name':'v1'})
    #     response = self.client.get(plist)
    #     self.assertEqual(response.status_code, 401) # not authorized shows working
    #     #self.assertEqual(response.status_code, 200)

    def test_organizational_code_list_api(self):
        plist = reverse('api_dispatch_list', kwargs={'resource_name': 'organization_type','api_name':'v1'})
        response = self.client.get(plist)
        self.assertEqual(response.status_code, 200)

    def test_organizational_code_list_api(self):
        plist = reverse('api_dispatch_list', kwargs={'resource_name': 'organization_type','api_name':'v1'})
        response = self.client.get(plist)
        self.assertEqual(response.status_code, 200)

    # def test_person_list_api(self):
    #     plist = reverse('api_dispatch_list', kwargs={'resource_name': 'person','api_name':'v1'})
    #     response = self.client.get(plist)
    #     self.assertEqual(response.status_code, 200)

    def test_person_json(self):
        #serializer = PersonFoafSerializer()
        ares = PersonResource(api_name='v1')
        request = HttpRequest()
        request.method = 'GET'


        #person = ares.obj_get( pk=self.aPerson.pk)
        person = Person.objects.get(pk=self.aPerson.pk)
        #ares_bundle = ares.build_bundle(obj=person,request=request)
        ares_bundle = ares.build_bundle(obj=person)
        json = ares.serialize(None,ares.full_dehydrate(ares_bundle),'application/json')

        print (json)
        self.assertTrue('"name": "last first"' in json)

    def test_person_foaf(self):

        ares = PersonResource(api_name='v1')
        request = HttpRequest()
        request.method = 'GET'


        #person = ares.obj_get( pk=self.aPerson.pk)
        person = Person.objects.get(pk=self.aPerson.pk)
        #ares_bundle = ares.build_bundle(obj=person,request=request)
        ares_bundle = ares.build_bundle(obj=person)
        xml_response = ares.serialize(None,ares.full_dehydrate(ares_bundle),'application/rdf+xml')
        print xml_response

        self.assertIn('<rdf:type rdf:resource="http://xmlns.com/foaf/0.1/person"/>', xml_response)
        self.assertIn('<foaf:name>Full Name</foaf:name>' , xml_response)
        # force fail for a while
        self.assertIn('xxxx' , xml_response)

    def test_organization_json(self):
        #serializer = PersonFoafSerializer()
        ares = OrganizationResource(api_name='v1')
        request = HttpRequest()
        request.method = 'GET'


        #person = ares.obj_get( pk=self.aPerson.pk)
        org = Organization.objects.get(pk=self.org2.pk)
        #ares_bundle = ares.build_bundle(obj=person,request=request)
        ares_bundle = ares.build_bundle(obj=org)
        json = ares.serialize(None,ares.full_dehydrate(ares_bundle),'application/json')

        print (json)
        self.assertTrue('"name": "org2"' in json)
        self.assertTrue('"name": "Org Name"' in json)

    def test_organization_foaf(self):

        ares = OrganizationResource(api_name='v1')
        request = HttpRequest()
        request.method = 'GET'


        #person = ares.obj_get( pk=self.aPerson.pk)
        #org = Organization.objects.get(pk=self.org2.pk)
        org = Organization.objects.get(name='Default Organization')
        #ares_bundle = ares.build_bundle(obj=person,request=request)
        ares_bundle = ares.build_bundle(obj=org)
        xml_response = ares.serialize(None,ares.full_dehydrate(ares_bundle),'application/rdf+xml')
        print xml_response

        self.assertIn('<rdf:type rdf:resource="http://xmlns.com/foaf/0.1/organization"/>', xml_response)
        self.assertIn('<foaf:name>org2</foaf:name>' , xml_response)
        self.assertIn('<foaf:img rdf:resource="http://www.example.com"/>' , xml_response)

        # force fail for a while
        self.assertIn('xxxx' , xml_response)

    def test_organization_association_rdf(self):

        ares = OrganizationAssociationResource(api_name='v1')
        request = HttpRequest()
        request.method = 'GET'


        #person = ares.obj_get( pk=self.aPerson.pk)
        #org = Organization.objects.get(pk=self.org2.pk)
        org = OrganizationAssociation.objects.get(organization__name="Default Organization")
        #ares_bundle = ares.build_bundle(obj=person,request=request)
        ares_bundle = ares.build_bundle(obj=org)
        ares_bundle = ares.full_dehydrate(ares_bundle) # not inline to help in debugging
        xml_response = ares.serialize(None,ares_bundle,'application/rdf+xml')
        print xml_response

        self.assertIn('<rdf:type rdf:resource="http://xmlns.com/foaf/0.1/organization"/>', xml_response)
        self.assertIn('<foaf:name>org2</foaf:name>' , xml_response)
        self.assertIn('<foaf:img rdf:resource="http://www.example.com"/>' , xml_response)

        # force fail for a while
        self.assertIn('xxxx' , xml_response)
