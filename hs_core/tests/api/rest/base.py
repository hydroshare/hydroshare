import socket

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource


class HSRESTTestCase(APITestCase):

    def setUp(self):
        self.hostname = socket.gethostname()
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

    def getResourceBag(self, res_id):
        """
        Get resource bag from iRODS, following redirects
        :param res_id: ID of resource whose bag should be fetched
        :return: Django test client response object
        """
        bag_url = "/hsapi/resource/{res_id}".format(res_id=res_id)
        response = self.client.get(bag_url)

        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)
        self.assertTrue('Location' in response)
        redir_url1 = response['Location'].replace('testserver', self.hostname)

        redir_response = self.client.get(redir_url1)
        self.assertEqual(redir_response.status_code, status.HTTP_302_FOUND)
        redir_url2 = response['Location'].replace('testserver', self.hostname)
        redir_response2 = self.client.get(redir_url2)

        bag_irods_url = redir_response2['Location'].replace('example.com', self.hostname)
        bag_response = self.client.get(bag_irods_url)
        self.assertEqual(bag_response.status_code, status.HTTP_200_OK)

        return bag_response

