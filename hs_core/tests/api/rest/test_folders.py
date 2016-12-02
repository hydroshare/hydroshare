import json
from pprint import pprint
from rest_framework import status

from django_irods.icommands import SessionException

from .base import HSRESTTestCase


class TestFolders(HSRESTTestCase):

    def test_create_folder(self):
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

        url2 = str.format('/hsapi/resource/{}/folders/foo/', res_id)

        # should not be able to ls non-existent folder
        response = self.client.get(url2, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND) 
        content = json.loads(response.content)
        self.assertEqual(content, 'Cannot list path')

        # should not be able to delete non-existent folder
        response = self.client.delete(url2, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST) 
        content = json.loads(response.content)
        self.assertEqual(content, "Cannot remove folder") 

        # create a folder
        response = self.client.put(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # should be able to create it again
        response = self.client.put(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # list that folder: should work, should be empty
        response = self.client.get(url2, {})
        pprint(response.content)
        content = json.loads(response.content)
        pprint(content) 
        self.assertEqual(len(content['folders']), 0)
        self.assertEqual(len(content['files']), 0)

        # delete that folder: should be possible
        response = self.client.delete(url2, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_file_in_folder(self):
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

        # create a folder 'foo'
        url2 = str.format('/hsapi/resource/{}/folders/foo/', res_id)
        response = self.client.put(url2, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # put a file into 'foo'
        params = {'file': ('cea.tif',
                           open('hs_core/tests/data/cea.tif'),
                           'image/tiff')}
        response = self.client.put(url2, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


