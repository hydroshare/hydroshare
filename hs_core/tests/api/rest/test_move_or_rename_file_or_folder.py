import os
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestPublicRenameEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicRenameEndpoint, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype, self.user, self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

        # create a folder 'foo'
        url2 = str.format('/hsapi/resource/{}/folders/foo/', self.pid)
        self.client.put(url2, {})

        # put a file 'test.txt' into folder 'foo'
        url2 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': (self.txt_file_name,
                           open(self.txt_file_path, 'rb'),
                           'text/plain')}
        self.client.post(url2, params)

        # put a file 'cea.tif' into folder 'foo'
        url3 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': (self.raster_file_name,
                           open(self.raster_file_path, 'rb'),
                           'image/tiff')}
        self.client.post(url3, params)

    def test_bad_requests(self):
        unzip_url = "/hsapi/resource/%s/functions/move-or-rename/" % self.pid
        response = self.client.post(unzip_url, {
            "source_path": " ",
            "target_path": "data/contents/foo"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(unzip_url, {
            "source_path": "data/contents/foo",
            "target_path": " "
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(unzip_url, {
            "target_path": "data/contents/foo"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response = self.client.post(unzip_url, {
            "source_path": "data/contents/foo"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_good_request(self):
        unzip_url = "/hsapi/resource/%s/functions/move-or-rename/" % self.pid
        response = self.client.post(unzip_url, {
            "source_path": "data/contents/foo",
            "target_path": "data/contents/bar"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
