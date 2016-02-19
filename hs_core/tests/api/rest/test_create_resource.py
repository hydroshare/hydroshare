import json

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource


class TestCreateResource(APITestCase):

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

        self.resources_to_delete = []

    def tearDown(self):
        for r in self.resources_to_delete:
            resource.delete_resource(r)

        self.user.delete()

    def test_post_resource_get_sysmeta(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # Get the resource system metadata to make sure the resource was
        # properly created.
        sysmeta_url = "/hsapi/sysmeta/{res_id}/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)

