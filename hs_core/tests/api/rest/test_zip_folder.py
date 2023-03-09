import os
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource

from .base import HSRESTTestCase


class TestPublicZipEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestPublicZipEndpoint, self).setUp()

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
        self.res = resource.create_resource(self.rtype, self.user, self.title, unpack_file=False)

        self.pid = self.res.short_id
        self.resources_to_delete.append(self.pid)

        # create a folder 'foo'
        url = str.format('/hsapi/resource/{}/folders/foo/', self.pid)
        self.client.put(url, {})

        # put a file 'test.txt' into folder 'foo'
        url2 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': ('text.txt',
                           open(self.txt_file_path, 'rb'),
                           'text/plain')}
        self.client.post(url2, params)

        # put a file 'cea.tif' into folder 'foo'
        url3 = str.format('/hsapi/resource/{}/files/foo/', self.pid)
        params = {'file': (self.raster_file_name,
                           open(self.raster_file_path, 'rb'),
                           'image/tiff')}
        self.client.post(url3, params)

    def test_zip_folder_bad_requests(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid

        response_no_path = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip"
        }, format="json")
        response_empty_path = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip"
        }, format="json")
        response_no_fname = self.client.post(zip_url, {
            "output_zip_file_name": " ",
            "input_coll_path": "/files/foo"
        }, format="json")
        response_empty_fname = self.client.post(zip_url, {
            "output_zip_file_name": "test.zip",
            "input_coll_path": " "
        }, format="json")

        self.assertEqual(response_no_path.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_empty_path.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_no_fname.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response_empty_fname.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zip_folder(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid
        response = self.client.post(zip_url, {
            "input_coll_path": "data/contents/foo",
            "output_zip_file_name": "test.zip",
            "remove_original_after_zip": False
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zip_aggregation(self):
        zip_url = "/hsapi/resource/%s/functions/zip-by-aggregation-file/" % self.pid
        raster_vrt_filename, _ = os.path.splitext(self.raster_file_name)
        raster_vrt_filename = f"{raster_vrt_filename}.vrt"
        response = self.client.post(zip_url, {
            "aggregation_path": f"data/contents/foo/{raster_vrt_filename}",
            "output_zip_file_name": "test.zip"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zip_folder_remove(self):
        zip_url = "/hsapi/resource/%s/functions/zip/" % self.pid
        response = self.client.post(zip_url, {
            "input_coll_path": "data/contents/foo",
            "output_zip_file_name": "test.zip",
            "remove_original_after_zip": True
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
