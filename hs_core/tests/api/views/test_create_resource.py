import os
import tempfile
import shutil

from django.contrib.sessions.middleware import SessionMiddleware
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.urlresolvers import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views import create_resource
from hs_core.testing import MockIRODSTestCaseMixin


class TestCreateResourceViewFunctions(MockIRODSTestCaseMixin, TestCase):
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

        self.factory = RequestFactory()

        self.temp_dir = tempfile.mkdtemp()

        # Make a text file
        self.txt_file_name = 'text.txt'
        self.txt_file_path = os.path.join(self.temp_dir, self.txt_file_name)
        txt = open(self.txt_file_path, 'w')
        txt.write("Hello World\n")
        txt.close()

    def tearDown(self):
        super(TestCreateResourceViewFunctions, self).tearDown()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_create_resource(self):
        # here we are testing the create_resource view function

        # test with no file upload
        post_data = {'resource-type': 'GenericResource',
                     'title': 'Test Generic Resource Creation',
                     'irods_federated': 'true'
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        res_id = response.url.split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        hydroshare.delete_resource(res_id)
        self.assertEqual(BaseResource.objects.count(), 0)

        # test with file upload
        post_data = {'resource-type': 'GenericResource',
                     'title': 'Test Generic Resource Creation',
                     'irods_federated': 'true',
                     'file': (self.txt_file_name, open(self.txt_file_path))
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        res_id = response.url.split('/')[2]
        self.assertEqual(BaseResource.objects.filter(short_id=res_id).exists(), True)
        hydroshare.delete_resource(res_id)

    def test_create_resource_failure(self):
        # here we are testing the create_resource view function

        self.assertEqual(BaseResource.objects.count(), 0)
        # test with non-existing resource type
        post_data = {'resource-type': 'BadResourceType',
                     'title': 'Test Generic Resource Creation',
                     'irods_federated': 'true'
                     }
        url = reverse('create_resource')
        request = self.factory.post(url, data=post_data)
        request.user = self.user
        self._set_request_message_attributes(request)
        self._add_session_to_request(request)

        response = create_resource(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # this should take back to create_resource.html page
        self.assertIn('<!doctype html>', response.content)
        self.assertEqual(BaseResource.objects.count(), 0)

    def _set_request_message_attributes(self, request):
        # the following 3 lines are for preventing error in unit test due to the view being
        # tested uses messaging middleware
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)

    def _add_session_to_request(self, request):
        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
