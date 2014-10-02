from tempfile import NamedTemporaryFile
import zipfile
import requests

__author__ = 'selimnairb@gmail.com'
"""
Tastypie REST API tests for resources modeled after: http://django-tastypie.readthedocs.org/en/latest/testing.html

"""
from tastypie.test import ResourceTestCase
from tastypie.test import TestApiClient

from django.contrib.auth.models import User
from hs_core import hydroshare
from hs_core.models import GenericResource

import logging

class ResourceTest(ResourceTestCase):

    def setUp(self):
        self.logger = logging.getLogger(__name__)

        self.api_client = TestApiClient()

        self.username = 'creator'
        self.password = 'mybadpassword'

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[]
        )
        self.user_url = '/hsapi/accounts/{0}/'.format(self.user_creator.username)

        self.api_client.client.login(username=self.username, password=self.password)

        # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='GenericResource',
            title='My resource',
            owner=self.user_creator,
            last_changed_by=self.user_creator
        )
        self.resource_url_base = '/hsapi/resource/'
        self.resource_url = '{0}{1}/'.format(self.resource_url_base, self.resource.short_id)

        self.post_data = {
            'title': 'My REST API-created resource',
            'resource_type' : 'GenericResource'
        }

    def tearDown(self):
        User.objects.all().delete()
        GenericResource.objects.all().delete()

    def get_credentials(self):
        k = self.create_basic(username=self.username, password=self.password)
        print k
        return k

    def test_resource_get(self):

        resp = self.api_client.get(self.resource_url)
        self.assertTrue(resp['Location'].endswith('.zip'))

    def test_resource_post(self):
        resp = self.api_client.post(self.resource_url_base, data=self.post_data )
        self.assertIn(resp.status_code, [201, 200])

        # PID comes back as body of response, but API client doesn't seem to be
        # parsing the response for us
        pid = str(resp).split('\n')[-1]
        new_resource_url = '{0}{1}/'.format(self.resource_url_base, pid)

        # Fetch the newly created resource
        resp = self.api_client.get(new_resource_url)
        self.assertTrue(resp['Location'].endswith('.zip'))


    def test_resource_put(self):
        new_data = {}
        new_data['title'] = 'My UPDATED REST API-created resource'

        resp = self.api_client.put(self.resource_url, data=new_data)
        self.assertIn(resp.status_code, ['202','204'])


    def test_resource_delete(self):
        x = self.api_client.delete(self.resource_url, format='json')
        self.assertIn(x.status_code, [202, 204, 301])
        self.assertHttpNotFound( self.api_client.get(self.resource_url, format='json'))
