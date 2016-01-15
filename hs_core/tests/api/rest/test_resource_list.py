import json

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource


class TestResourceList(APITestCase):

    def setUp(self):
        self.maxDiff = None
        self.client = APIClient()

        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False)

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.delete()

    def test_resource_list(self):

        new_res = resource.create_resource('GenericResource',
                                           self.user,
                                           'My Test Resource')
        pid = new_res.short_id

        response = self.client.get('/hsapi/resourceList/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], pid)

    def test_resource_list_by_type(self):

        gen_res = resource.create_resource('GenericResource',
                                           self.user,
                                           'My Test Resource')
        gen_pid = gen_res.short_id

        raster = open('hs_core/tests/data/cea.tif')
        geo_res = resource.create_resource('RasterResource',
                                           self.user,
                                           'My raster resource',
                                           files=(raster,))
        geo_pid = geo_res.short_id

        app_res = resource.create_resource('ToolResource',
                                           self.user,
                                           'My Test App Resource')
        app_pid = app_res.short_id

        response = self.client.get('/hsapi/resourceList/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)
        self.assertEqual(content['results'][0]['resource_id'], gen_pid)
        self.assertEqual(content['results'][1]['resource_id'], geo_pid)
        self.assertEqual(content['results'][2]['resource_id'], app_pid)

        # Filter by type (single)
        response = self.client.get('/hsapi/resourceList/', {'type': 'RasterResource'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 1)
        self.assertEqual(content['results'][0]['resource_id'], geo_pid)

        # Filter by type (multiple)
        response = self.client.get('/hsapi/resourceList/', {'type': ['RasterResource', 'ToolResource']},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)
        self.assertEqual(content['results'][0]['resource_id'], geo_pid)
        self.assertEqual(content['results'][1]['resource_id'], app_pid)
