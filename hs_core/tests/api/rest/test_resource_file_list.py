import os
import json
import zipfile
import tempfile
import shutil

from django.contrib.auth.models import Group

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare import users
from hs_core.hydroshare import resource

from hs_core.tests.api.utils import MyTemporaryUploadedFile


class TestResourceList(APITestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
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

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.tmp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

        self.raster_file_name = 'cea.tif'
        self.raster_file_path = 'hs_core/tests/data/cea.tif'

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        self.user.uaccess.delete()
        self.user.delete()
        self.group.delete()

    def test_resource_file_list(self):

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
        pid = res.short_id

        response = self.client.get("/hsapi/resource/{pid}/file_list/".format(pid=pid),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['count'], 2)
        self.assertEqual(os.path.basename(content['results'][0]['url']), self.txt_file_name)
        self.assertEqual(os.path.basename(content['results'][1]['url']), self.raster_file_name)
