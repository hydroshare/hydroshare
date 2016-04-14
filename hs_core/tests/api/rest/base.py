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
        self.resource_url = "http://example.com/resource/{res_id}/"
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

    def getResourceBag(self, res_id, exhaust_stream=True):
        """Get resource bag from iRODS, following redirects.

        :param res_id: ID of resource whose bag should be fetched
        :param exhaust_stream: If True, the response returned
           will have its stream_content exhausted.  This prevents
           an error that causes the Docker container to exit when tests
           are run with an external web server.
        :return: Django test client response object
        """
        url = "/hsapi/resource/{res_id}".format(res_id=res_id)
        return self._get_file_irods(url, exhaust_stream)

    def getResourceFile(self, res_id, file_name, exhaust_stream=True):
        """Get resource file from iRODS, following redirects

        :param res_id: ID of resource whose resource file should be fetched
        :param file_name: Name of the file to fetch (just the filename, not the full path)
        :param exhaust_stream: If True, the response returned
           will have its stream_content exhausted.  This prevents
           an error that causes the Docker container to exit when tests
           are run with an external web server.
        :return: Django test client response object
        """
        url = "/hsapi/resource/{res_id}/files/{file_name}".format(res_id=res_id,
                                                                  file_name=file_name)
        return self._get_file_irods(url, exhaust_stream)

    def _get_file_irods(self, url, exhaust_stream=True):
        response = self.client.get(url, follow=True)
        self.assertTrue(response.status_code, status.HTTP_200_OK)

        # Exhaust the file stream so that WSGI doesn't get upset (this causes the Docker container to exit)
        if exhaust_stream:
            for l in response.streaming_content:
                pass

        return response

    def getScienceMetadata(self, res_id):
        """Get sciencematadata.xml from iRODS, following redirects

        :param res_id: ID of resource whose science metadata should be fetched
        :return: Django test client response object
        """
        bag_url = "/hsapi/scimeta/{res_id}/".format(res_id=res_id)
        response = self.client.get(bag_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue('Location' in response)
        xml_irods_url = response['Location'].replace('example.com', self.hostname)
        xml_response = self.client.get(xml_irods_url)
        self.assertEqual(xml_response.status_code, status.HTTP_200_OK)
        self.assertEqual(xml_response['Content-Type'], 'application/xml')
        self.assertTrue(int(xml_response['Content-Length']) > 0)
