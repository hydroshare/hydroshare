__author__ = 'shaunjl'

"""
Tastypie REST API tests for resourceFileCRUD.as_view

"""
from tastypie.test import ResourceTestCase
from tastypie.test import TestApiClient
from django.contrib.auth.models import User
from hs_core import hydroshare
from tastypie.serializers import Serializer

from hs_core.models import GenericResource

class ResourceTest(ResourceTestCase):
    serializer= Serializer()

    def setUp(self):
        self.api_client = TestApiClient()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.user = hydroshare.create_account(
            'shaun@gmail.com',
            username=self.username,
            password=self.password,
            first_name='User0_FirstName',
            last_name='User0_LastName',
        )

        self.api_client.client.login(username=self.username, password=self.password)

        self.url_proto = '/hsapi/resource/{0}/files/{1}/'

        self.filename = 'test.txt'


    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def test_resource_file_get(self):

        myfile = open(self.filename, 'w')
        myfile.write('hello world!\n')
        myfile.close()
        myfile = open(self.filename, 'r')

        res1 = hydroshare.create_resource('GenericResource', self.user, 'res1')

        hydroshare.add_resource_files(res1.short_id, myfile)
        url = self.url_proto.format(res1.short_id, self.filename)

        resp = self.api_client.get(url)
        self.assertIn(resp.status_code, [201, 200])


    def test_resource_file_put(self):

        myfile = open(self.filename, 'w')
        myfile.write('hello world!\n')
        myfile.close()
        myfile = open(self.filename, 'r')

        res1 = hydroshare.create_resource('GenericResource', self.user, 'res1')

        hydroshare.add_resource_files(res1.short_id, myfile)

        mynewfile = open(self.filename, 'w')
        mynewfile.write('anyone there?\n')
        mynewfile.close()
        mynewfile = open(self.filename, 'r')

        url = self.url_proto.format(res1.short_id, self.filename)

        put_data = { 'resource_file': mynewfile
        }

        resp = self.api_client.put(url, data=put_data)
        self.assertHttpAccepted(resp)

        resp = self.api_client.get(url)
        self.assertIn(resp.status_code, [201, 200])


    def test_resource_file_post(self):

        myfile = open(self.filename, 'w')
        myfile.write('hello world!\n')
        myfile.close()
        myfile = open(self.filename, 'r')

        res1 = hydroshare.create_resource('GenericResource', self.user, 'res1')

        post_data = { 'resource_file': myfile
        }

        url = self.url_proto.format(res1.short_id, self.filename)

        resp = self.api_client.post(url, data=post_data)
        self.assertHttpAccepted(resp)

        resp = self.api_client.get(url)
        self.assertIn(resp.status_code, [201, 200])


    def test_resource_file_delete(self):

        myfile = open(self.filename, 'w')
        myfile.write('hello world!\n')
        myfile.close()
        myfile = open(self.filename, 'r')

        res1 = hydroshare.create_resource('GenericResource', self.user, 'res1')

        hydroshare.add_resource_files(res1.short_id, myfile)
        url = self.url_proto.format(res1.short_id, self.filename)

        resp = self.api_client.delete(url)

        self.assertIn(resp.status_code, [200, 202, 204])
        self.assertHttpNotFound( self.api_client.get(url, format='json') )
