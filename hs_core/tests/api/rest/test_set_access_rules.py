import json

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource


class TestSetAccessRules(APITestCase):

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

    def test_set_access_rules(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        keywords = ('foo', 'bar')
        abstract = 'This is a resource used for testing /hsapi/accessRules'
        new_res = resource.create_resource(rtype,
                                           self.user,
                                           title,
                                           keywords=keywords)
        new_res.metadata.create_element('description', abstract=abstract)
        res_id = new_res.short_id

        sysmeta_url = "/hsapi/sysmeta/{res_id}/".format(res_id=res_id)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], rtype)
        self.assertEqual(content['resource_title'], title)
        self.assertFalse(content['public'])

        access_url = "/hsapi/resource/accessRules/{res_id}/".format(res_id=res_id)
        response = self.client.put(access_url, {'public': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertTrue(content['public'])