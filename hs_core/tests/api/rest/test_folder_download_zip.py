import json
import os
import tempfile

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase
from datetime import date


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

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title,
                                       unpack_file=False)

        self.pid = res.short_id
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

    def test_folder_download_rest(self):
        date_folder = (date.today()).strftime('%Y-%m-%d')
        zip_download_url = "/resource/{pid}/data/contents/foo".format(pid=self.pid)
        response = self.client.get(zip_download_url, format="json")
        # becasue of the redirect to the internal url, the status code is 301
        self.assertEqual(response.status_code, status.HTTP_301_MOVED_PERMANENTLY)
        zip_download_url = "/django_irods/rest_download/zips/{pid}/data/contents/foo".format(
            pid=self.pid)
        response = self.client.get(zip_download_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content)
        task_id = response_json["task_id"]
        download_path = response_json["download_path"]
        self.assertTrue(len(task_id) > 0, msg='ensure a task_id is returned for async zipping')
        download_split = download_path.split("/")
        self.assertEqual("django_irods", download_split[1])
        self.assertEqual("rest_download", download_split[2])
        self.assertEqual("zips", download_split[3])
        self.assertEqual(date_folder, download_split[4])
        self.assertEqual(self.pid, download_split[5])
        # index 5 is the random folder
        self.assertEqual("data", download_split[7])
        self.assertEqual("contents", download_split[8])
        self.assertEqual("foo.zip", download_split[9])

        response = self.client.get(zip_download_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content)
        self.assertNotEqual(((response_json["download_path"])[5]).split("/"), download_split[5])
