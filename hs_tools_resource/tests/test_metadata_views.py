__author__ = 'hydro'
import unittest

from tastypie.test import ResourceTestCase
from tastypie.test import TestApiClient
from django.test import Client
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import BaseResource
from tastypie.serializers import Serializer
import urllib
import logging
from hs_tools_resource.models import ToolResource
from decimal import Decimal


class TestCreateMetadataViews(ResourceTestCase):

    def setUp(self):
        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.api_client.login(username=self.username, password=self.password)

                # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='ToolResource',
            title='My resource',
            owner=self.user_creator,
        )


    def tearDown(self):
        User.objects.all().delete()
        ToolResource.objects.all().delete()

    @unittest.skip
    def test_create_request_url(self):
        self.assertEqual(len(self.resource.metadata.url_bases.all()), 0)
        post_data = {
            'value': 'www.example.com',
        }
        url = "/hsapi/_internal/"+self.resource.short_id+"/RequestUrlBase/add-metadata/"
        resp = self.api_client.post(url,
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.url_bases.all()), 1)
        self.assertEqual(self.resource.metadata.url_bases.all()[0].value, 'www.example.com')

    @unittest.skip
    def test_create_fee(self):
        self.assertEqual(len(self.resource.metadata.fees.all()), 0)
        post_data = {
            'description': 'fee description',
            'value': Decimal('55')
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/Fee/add-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.fees.all()), 1)
        self.assertEqual(self.resource.metadata.fees.all()[0].description, 'fee description')
        self.assertEqual(self.resource.metadata.fees.all()[0].value, Decimal('55'))

    @unittest.skip
    def test_create_resource_types(self):
        self.assertEqual(len(self.resource.metadata.res_types.all()), 0)
        post_data = {
            'tool_res_type': 'ref_ts'
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/ToolResourceType/add-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.res_types.all()), 1)
        self.assertEqual(self.resource.metadata.res_types.all()[0].tool_res_type, 'ref_ts')

    @unittest.skip
    def test_create_tool_version(self):
        self.assertEqual(len(self.resource.metadata.versions.all()), 0)
        post_data = {
            'value': '5'
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/ToolVersion/add-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(len(self.resource.metadata.versions.all()), 1)
        self.assertEqual(self.resource.metadata.versions.all()[0].value, '5')



class TestUpdateMetadataViews(ResourceTestCase):

    def setUp(self):
        self.serializer = Serializer()
        self.logger = logging.getLogger(__name__)

        self.api_client = Client()

        self.username = 'creator'
        self.password = 'mybadpassword'

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')

        # create a user to be used for creating the resource
        self.user_creator = hydroshare.create_account(
            'creator@hydroshare.org',
            username=self.username,
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            password=self.password,
            groups=[self.group]
        )

        self.api_client.login(username=self.username, password=self.password)

                # create a resource
        self.resource = hydroshare.create_resource(
            resource_type='ToolResource',
            title='My resource',
            owner=self.user_creator,
        )
        self.url1 = 'www.one.com'
        self.url2 = 'www.two.com'
        self.res1 = 'res_type1'
        self.res2 = 'res_type2'
        self.desc1 = 'description1'
        self.desc2 = 'description2'
        self.fee1 = Decimal('1')
        self.fee2 = Decimal('2')
        self.version1 = '1'
        self.version2 = '2'
        hydroshare.resource.create_metadata_element(self.resource.short_id,
                                                    'RequestUrlBase',
                                                    value=self.url1
                                                    )

        hydroshare.resource.create_metadata_element(self.resource.short_id,
                                                    'ToolResourceType',
                                                    tool_res_type=self.res1
                                                    )

        hydroshare.resource.create_metadata_element(self.resource.short_id,
                                                    'Fee',
                                                    description=self.desc1,
                                                    value=self.fee1
                                                    )

        hydroshare.resource.create_metadata_element(self.resource.short_id,
                                                    'ToolVersion',
                                                    value=self.version1
                                                    )




    def tearDown(self):
        User.objects.all().delete()
        ToolResource.objects.all().delete()

    @unittest.skip
    def test_update_request_url(self):
        self.assertEqual(len(self.resource.metadata.url_bases.all()), 1)
        self.assertEqual(self.resource.metadata.url_bases.all()[0].value, self.url1)
        post_data = {
            'value': self.url2,
        }
        url = "/hsapi/_internal/"+self.resource.short_id+"/RequestUrlBase/" + \
              str(self.resource.metadata.url_bases.all()[0].id)+"/update-metadata/"
        resp = self.api_client.post(url,
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.url_bases.all()), 1)
        self.assertEqual(self.resource.metadata.url_bases.all()[0].value, self.url2)

    @unittest.skip
    def test_update_fee(self):
        self.assertEqual(len(self.resource.metadata.fees.all()), 1)
        self.assertEqual(self.resource.metadata.fees.all()[0].description, self.desc1)
        self.assertEqual(self.resource.metadata.fees.all()[0].value, self.fee1)
        post_data = {
            'description': self.desc2,
            'value': self.fee2
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/Fee/"+
                                    str(self.resource.metadata.fees.all()[0].id)+"/update-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.fees.all()), 1)
        self.assertEqual(self.resource.metadata.fees.all()[0].description, self.desc2)
        self.assertEqual(self.resource.metadata.fees.all()[0].value, self.fee2)

    @unittest.skip
    def test_update_resource_types(self):
        self.assertEqual(len(self.resource.metadata.res_types.all()), 1)
        self.assertEqual(self.resource.metadata.res_types.all()[0].tool_res_type, self.res1)
        post_data = {
            'tool_res_type': self.res2
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/ToolResourceType/"+
                                    str(self.resource.metadata.res_types.all()[0].id)+"/update-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(self.resource.metadata.res_types.all()), 1)
        self.assertEqual(self.resource.metadata.res_types.all()[0].tool_res_type, self.res2)

    @unittest.skip
    def test_update_tool_version(self):
        self.assertEqual(len(self.resource.metadata.versions.all()), 1)
        self.assertEqual(self.resource.metadata.versions.all()[0].value, self.version1)
        post_data = {
            'value': self.version2
        }
        resp = self.api_client.post("/hsapi/_internal/"+self.resource.short_id+"/ToolVersion/"+
                                    str(self.resource.metadata.versions.all()[0].id)+"/update-metadata/",
                                    post_data,
                                    follow=True,
                                    HTTP_REFERER='http://localhost:8000/resource/'+self.resource.short_id)
        self.assertEqual(len(self.resource.metadata.versions.all()), 1)
        self.assertEqual(self.resource.metadata.versions.all()[0].value, self.version2)
