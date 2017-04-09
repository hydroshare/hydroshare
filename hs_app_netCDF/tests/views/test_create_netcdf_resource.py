import os
import shutil

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
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
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

        self.netcdf_file_name = 'netcdf_valid.nc'
        self.netcdf_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_file_name)
        target_temp_netcdf_file = os.path.join(self.temp_dir, self.netcdf_file_name)
        shutil.copy(self.netcdf_file, target_temp_netcdf_file)
        self.netcdf_file_obj = open(target_temp_netcdf_file, 'r')

        self.netcdf_bad_file_name = 'netcdf_invalid.nc'
        self.netcdf_bad_file = 'hs_app_netCDF/tests/{}'.format(self.netcdf_bad_file_name)
        target_temp_bad_netcdf_file = os.path.join(self.temp_dir, self.netcdf_bad_file_name)
        shutil.copy(self.netcdf_bad_file, target_temp_bad_netcdf_file)
        self.netcdf_bad_file_obj = open(target_temp_bad_netcdf_file, 'r')

    def test_create_resource(self):
        # here we are testing the create_resource view function

        # test with no file upload
        post_data = {'resource-type': 'NetcdfResource',
                     'title': 'Test NetCDF Resource Creation',
                     'irods_federated': 'true'
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        res_id = response.url.split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        hydroshare.delete_resource(res_id)
        self.assertEqual(BaseResource.objects.count(), 0)

        # test with file upload
        self.assertEqual(ResourceFile.objects.count(), 0)
        post_data = {'resource-type': 'NetcdfResource',
                     'title': 'Test NetCDF Resource Creation',
                     'irods_federated': 'true',
                     'files': (self.netcdf_file_name, open(self.netcdf_file))
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        res_id = response.url.split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        # there should be 2 files (nc and txt) - successful metadata extraction
        self.assertEqual(ResourceFile.objects.count(), 2)

        hydroshare.delete_resource(res_id)

    def test_create_resource_with_invalid_file(self):
        # here we are testing the create_resource view function

        self.assertEqual(BaseResource.objects.count(), 0)
        self.assertEqual(ResourceFile.objects.count(), 0)
        # test with bad nc file - this file should not be uploaded and the resource
        # is also not created
        post_data = {'resource-type': 'NetcdfResource',
                     'title': 'Test NetCDF Resource Creation',
                     'irods_federated': 'true',
                     'files': (self.netcdf_bad_file_name,
                               open(self.netcdf_bad_file))
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # this should take back to create_resource.html page as resource was not created
        self.assertIn('<!doctype html>', response.content)
        self.assertEqual(BaseResource.objects.count(), 0)
