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
from hs_file_types.models import GenericLogicalFile


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

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.temp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestCreateResourceViewFunctions, self).tearDown()

    def test_create_resource(self):
        # here we are testing the create_resource view function

        # test with no file upload
        post_data = {'resource-type': 'CompositeResource',
                     'title': 'Test Composite Resource Creation'
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

        # at this point there should not be any resource file
        self.assertEqual(ResourceFile.objects.count(), 0)
        # at this point there should not be any generic logical file
        self.assertEqual(GenericLogicalFile.objects.count(), 0)
        post_data = {'resource-type': 'CompositeResource',
                     'title': 'Test Composite Resource Creation',
                     'files': (self.txt_file_name, open(self.txt_file_path), 'text/plain')
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
        # at this point there should 1 resource file
        self.assertEqual(ResourceFile.objects.count(), 1)
        # at this point there should not be any generic logical file as we not more
        # by default making any uploaded file as part of generic logical file
        self.assertEqual(GenericLogicalFile.objects.count(), 0)

        hydroshare.delete_resource(res_id)
