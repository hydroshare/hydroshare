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

        self.odm2_sqlite_file_name = 'ODM2_Multi_Site_One_Variable.sqlite'
        self.odm2_sqlite_file = 'hs_app_timeseries/tests/{}'.format(self.odm2_sqlite_file_name)
        target_temp_sqlite_file = os.path.join(self.temp_dir, self.odm2_sqlite_file_name)
        shutil.copy(self.odm2_sqlite_file, target_temp_sqlite_file)
        self.odm2_sqlite_file_obj = open(target_temp_sqlite_file, 'r')

        self.odm2_sqlite_invalid_file_name = 'ODM2_invalid.sqlite'
        self.odm2_sqlite_invalid_file = 'hs_app_timeseries/tests/{}'.format(
            self.odm2_sqlite_invalid_file_name)
        target_temp_sqlite_invalid_file = os.path.join(self.temp_dir,
                                                       self.odm2_sqlite_invalid_file_name)
        shutil.copy(self.odm2_sqlite_invalid_file, target_temp_sqlite_invalid_file)
        self.odm2_sqlite_invalid_file_obj = open(target_temp_sqlite_invalid_file, 'r')

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestCreateResourceViewFunctions, self).tearDown()

    def test_create_resource(self):
        # here we are testing the create_resource view function

        # test with no file upload
        post_data = {'resource-type': 'TimeSeriesResource',
                     'title': 'Test Time Series Resource Creation',
                     'irods_federated': 'true'
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
        post_data = {'resource-type': 'TimeSeriesResource',
                     'title': 'Test Time Series Resource Creation',
                     'irods_federated': 'true',
                     'files': (self.odm2_sqlite_file_name, open(self.odm2_sqlite_file))
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
        self.assertEqual(ResourceFile.objects.count(), 1)
        ts_resource = BaseResource.objects.filter(short_id=res_id).first()
        # check that the resource title got updated due to metadata extraction as part of resource
        # creation
        self.assertEqual(ts_resource.metadata.title.value,
                         "Water temperature data from the Little Bear River, UT")
        hydroshare.delete_resource(res_id)

    def test_create_resource_with_invalid_file(self):
        # here we are testing the create_resource view function

        self.assertEqual(BaseResource.objects.count(), 0)
        self.assertEqual(ResourceFile.objects.count(), 0)
        # test with bad sqlite file - this file should not be uploaded
        post_data = {'resource-type': 'TimeSeriesResource',
                     'title': 'Test Time Series Resource Creation',
                     'irods_federated': 'true',
                     'files': (self.odm2_sqlite_invalid_file_name,
                               open(self.odm2_sqlite_invalid_file))
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
        # that bad sqlite file was not uploaded
        self.assertEqual(ResourceFile.objects.count(), 0)
        hydroshare.delete_resource(res_id)
