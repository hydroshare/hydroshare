import os
import shutil
import json

from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.models import BaseResource, ResourceFile
from hs_core.views import create_resource
from hs_core.testing import MockIRODSTestCaseMixin, ViewTestCase


class TestCreateResourceViewFunctions(MockIRODSTestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestCreateResourceViewFunctions, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Resource Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.user = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.raster_tif_file_name = 'raster_tif_valid.tif'
        self.raster_tif_file = 'hs_geo_raster_resource/tests/{}'.format(self.raster_tif_file_name)
        target_temp_raster_tif_file = os.path.join(self.temp_dir, self.raster_tif_file_name)
        shutil.copy(self.raster_tif_file, target_temp_raster_tif_file)
        self.raster_tif_file_obj = open(target_temp_raster_tif_file, 'r')

        self.raster_bad_tif_file_name = 'raster_tif_invalid.tif'
        self.raster_bad_tif_file = 'hs_geo_raster_resource/tests/{}'.format(
            self.raster_bad_tif_file_name)
        target_temp_raster_bad_tif_file = os.path.join(self.temp_dir, self.raster_bad_tif_file_name)
        shutil.copy(self.raster_bad_tif_file, target_temp_raster_bad_tif_file)
        self.raster_bad_tif_file_obj = open(target_temp_raster_bad_tif_file, 'r')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestCreateResourceViewFunctions, self).tearDown()

    def test_create_resource(self):
        # here we are testing the create_resource view function

        # test with no file upload
        post_data = {'resource-type': 'RasterResource',
                     'title': 'Test Raster Resource Creation',
                     'irods_federated': 'false'
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content)
        self.assertEqual(json_content['status'], 'success')
        res_id = json_content['resource_url'].split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        hydroshare.delete_resource(res_id)
        self.assertEqual(BaseResource.objects.count(), 0)

        # test with file upload
        self.assertEqual(ResourceFile.objects.count(), 0)
        post_data = {'resource-type': 'RasterResource',
                     'title': 'Test Raster Resource Creation',
                     'irods_federated': 'false',
                     'files': (self.raster_tif_file_name, open(self.raster_tif_file))
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content)
        self.assertEqual(json_content['status'], 'success')
        self.assertEqual(json_content['file_upload_status'], 'success')
        res_id = json_content['resource_url'].split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        # there should be 2 files (tif and vrt) - successful metadata extraction
        self.assertEqual(ResourceFile.objects.count(), 2)

        hydroshare.delete_resource(res_id)

    def test_create_resource_with_invalid_file(self):
        # here we are testing the create_resource view function

        self.assertEqual(BaseResource.objects.count(), 0)
        self.assertEqual(ResourceFile.objects.count(), 0)
        # test with bad tif file - this file should not be uploaded
        post_data = {'resource-type': 'RasterResource',
                     'title': 'Test Raster Resource Creation',
                     'irods_federated': 'false',
                     'files': (self.raster_bad_tif_file_name,
                               open(self.raster_bad_tif_file))
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        json_content = json.loads(response.content)
        self.assertEqual(json_content['status'], 'success')
        self.assertEqual(json_content['file_upload_status'], 'error')
        res_id = json_content['resource_url'].split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        # test that the bad tif file was not uploaded
        self.assertEqual(ResourceFile.objects.count(), 0)
        hydroshare.delete_resource(res_id)
