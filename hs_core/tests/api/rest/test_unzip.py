import os
import tempfile
import zipfile

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.tests.api.utils import MyTemporaryUploadedFile

from .base import HSRESTTestCase


class TestPublicUnzipEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicUnzipEndpoint, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

        # Make a zip file
        zip_path = os.path.join(self.tmp_dir, 'test.zip')
        with zipfile.ZipFile(zip_path, 'w') as zfile:
            zfile.write(self.raster_file_path)
            zfile.write(self.txt_file_path)

        # Create a resource with zipfile, do not un-pack
        payload = MyTemporaryUploadedFile(open(zip_path, 'rb'), name=zip_path,
                                          content_type='application/zip',
                                          size=os.stat(zip_path).st_size)

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title, files=(payload,),
                                       unpack_file=False)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # create a folder 'foo'
        url2 = str.format('/hsapi/resource/{}/folders/foo/', self.pid)
        self.client.put(url2, {})

        # put the file 'test.zip' into folder 'foo'
        url4 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': (payload,)}
        self.client.post(url4, params)

    def test_unzip(self):
        unzip_url = "/hsapi/resource/%s/functions/unzip/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"remove_original_zip": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        list_url = "/hsapi/resource/%s/folders/test/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unzip_url = "/hsapi/resource/%s/functions/unzip/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # second run should unzip to another folder
        list_url = "/hsapi/resource/%s/folders/test-1/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unzip_overwrite(self):
        unzip_url = "/hsapi/resource/%s/functions/unzip/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"remove_original_zip": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unzip_url = "/hsapi/resource/%s/functions/unzip/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"overwrite": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        list_url = "/hsapi/resource/%s/folders/test/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # overwrite shouldn't write to a new folder
        list_url = "/hsapi/resource/%s/folders/test-1/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deep_unzip(self):
        unzip_url = "/hsapi/resource/%s/functions/unzip/foo/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"remove_original_zip": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        list_url = "/hsapi/resource/%s/folders/foo/test/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unzip_url = "/hsapi/resource/%s/functions/unzip/foo/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # second run should unzip to another folder
        list_url = "/hsapi/resource/%s/folders/foo/test-1/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_deep_unzip_overwrite(self):
        unzip_url = "/hsapi/resource/%s/functions/unzip/foo/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"remove_original_zip": "false"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        unzip_url = "/hsapi/resource/%s/functions/unzip/foo/test.zip/" % self.pid
        response = self.client.post(unzip_url, data={"overwrite": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        list_url = "/hsapi/resource/%s/folders/foo/test/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # overwrite shouldn't write to a new folder
        list_url = "/hsapi/resource/%s/folders/foo/test-1/" % self.pid
        response = self.client.get(list_url, data={})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unzip_unsuccessful(self):
        unzip_url = "/hsapi/resource/%s/functions/unzip/badpath/" % self.pid
        response = self.client.post(unzip_url, data={})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
