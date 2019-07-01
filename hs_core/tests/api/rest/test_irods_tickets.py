import json
from rest_framework import status
from .base import HSRESTTestCase


class TestTickets(HSRESTTestCase):

    def test_folder_ticket(self):
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

        # should be able to get read ticket for base folder
        url2 = str.format('/hsapi/resource/{}/ticket/read/data/contents/', res_id)
        response = self.client.get(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        ticket_id = content['ticket_id']

        # should be able to list ticket
        url3 = str.format('/hsapi/resource/{}/ticket/{}/', res_id, ticket_id)
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should be able to delete ticket
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should not be able to delete a ticket twice
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # should not be able to list a deleted ticket
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_file_ticket(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}

        # should be able to create resource
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # should be able to get read ticket for file
        url2 = str.format('/hsapi/resource/{}/ticket/read/data/contents/cea/cea.tif/', res_id)
        response = self.client.get(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        ticket_id = content['ticket_id']

        # should be able to list ticket
        url3 = str.format('/hsapi/resource/{}/ticket/{}/', res_id, ticket_id)
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should be able to delete ticket
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should not be able to delete a ticket twice
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # should not be able to list a deleted ticket
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_bag_ticket(self):
        rtype = 'GenericResource'
        title = 'My Test resource'
        params = {'resource_type': rtype,
                  'title': title,
                  'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}

        # should be able to create resource
        url = '/hsapi/resource/'
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        res_id = content['resource_id']
        self.resources_to_delete.append(res_id)

        # should be able to get read ticket for bag: no write option
        url2 = str.format('/hsapi/resource/{}/ticket/bag/', res_id)
        response = self.client.get(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        ticket_id = content['ticket_id']

        # should be able to list ticket
        url3 = str.format('/hsapi/resource/{}/ticket/{}/', res_id, ticket_id)
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should be able to delete ticket
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['ticket_id'], ticket_id)

        # should not be able to delete a ticket twice
        response = self.client.delete(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # should not be able to list a deleted ticket
        response = self.client.get(url3, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
