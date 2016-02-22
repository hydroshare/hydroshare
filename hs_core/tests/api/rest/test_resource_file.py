import os
import json
import zipfile
import tempfile
import shutil

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.tests.api.utils import MyTemporaryUploadedFile
from .base import HSRESTTestCase


class TestResourceFile(HSRESTTestCase):

    def setUp(self):
        super(TestResourceFile, self).setUp()

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
        res = resource.create_resource('GenericResource',
                                       self.user,
                                       'My Test resource',
                                       files=(payload,),
                                       unpack_file=True)
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

        super(TestResourceFile, self).tearDown()

    def test_resource_file_list(self):
        response = self.client.get("/hsapi/resource/{pid}/file_list/".format(pid=self.pid),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)
        self.assertEqual(os.path.basename(content['results'][0]['url']), self.txt_file_name)
        self.assertEqual(os.path.basename(content['results'][1]['url']), self.raster_file_name)

    def test_get_resource_file(self):
        file_response = self.getResourceFile(self.pid, self.txt_file_name)

    def test_create_resource_file(self):
        # Make a new text file
        txt_file_name = 'text2.txt'
        txt_file_path = os.path.join(self.tmp_dir, txt_file_name)
        txt = open(txt_file_path, 'w')
        txt.write("Hello World, again.\n")
        txt.close()
        # Upload the new resource file
        params = {'file': (txt_file_name,
                           open(txt_file_path),
                           'text/plain')}
        url = "/hsapi/resource/{pid}/files/".format(pid=self.pid)
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        self.assertEquals(content['resource_id'], self.pid)

        # Make sure the new file appears in the file list
        response = self.client.get("/hsapi/resource/{pid}/file_list/".format(pid=self.pid),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 3)
        self.assertEqual(os.path.basename(content['results'][0]['url']), txt_file_name)
