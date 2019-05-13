import json
from rest_framework import status
from hs_core.models import ResourceFile
from hs_core.models import get_path


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

        # should not be able to create the same folder again
        response = self.client.put(url2, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # list that folder: should work, should be empty
        response = self.client.get(url2, {})
        content = json.loads(response.content)
        self.assertEqual(len(content['folders']), 0)
        self.assertEqual(len(content['files']), 0)

        # delete that folder: should be possible
        response = self.client.delete(url2, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # should not be able to ls non-existent folder
        response = self.client.get(url2, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        content = json.loads(response.content)
        self.assertEqual(content, 'Cannot list path')

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

        # create a folder 'foo/bar'
        url3 = url2 + 'bar/'
        response = self.client.put(url3, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # put a file 'test.txt' into folder 'foo'
        url4 = str.format('/hsapi/resource/{}/files/foo/', res_id)
        params = {'file': ('test.txt',
                           open('hs_core/tests/data/test.txt'),
                           'text/plain')}
        response = self.client.post(url4, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        resfile = ResourceFile.objects.get(file_folder='foo')
        path = get_path(resfile, 'test.txt')
        self.assertEqual(path,
                         str.format("{}/data/contents/foo/test.txt",
                                    res_id))

        # list that folder: should contain one file and one folder
        response = self.client.get(url2, {})
        content = json.loads(response.content)
        self.assertEqual(len(content['folders']), 1)
        self.assertEqual(content['folders'][0], 'bar')
        self.assertEqual(len(content['files']), 1)
        self.assertEqual(content['files'][0], 'test.txt')
