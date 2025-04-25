import os
import shutil
import json

from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.models import BaseResource
from hs_core.views import delete_resource
from hs_core.testing import MockS3TestCaseMixin, ViewTestCase


class TestDeleteResource(MockS3TestCaseMixin, ViewTestCase):
    def setUp(self):
        super(TestDeleteResource, self).setUp()
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
        self.gen_res = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Resource Delete Testing'
        )

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(TestDeleteResource, self).tearDown()

    def test_delete_resource(self):
        # here we are testing the delete_resource view function

        self.assertEqual(BaseResource.objects.count(), 1)
        url_params = {'shortkey': self.gen_res.short_id, 'usertext': "DELETE"}
        url = reverse('delete_resource', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_resource(request, shortkey=self.gen_res.short_id, usertext="DELETE")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_dict = json.loads(response.content.decode())
        self.assertNotEqual(response_dict['status'], 'Failed')
        self.assertEqual(BaseResource.objects.count(), 0)

    def test_delete_resource_bad_usertext(self):
        # test a 400 is returned when usertext path parameter is not equal to DELETE
        self.assertEqual(BaseResource.objects.count(), 1)
        url_params = {'shortkey': self.gen_res.short_id, "usertext": "delete"}
        url = reverse('delete_resource', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.user
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.set_request_message_attributes(request)
        self.add_session_to_request(request)
        response = delete_resource(request, shortkey=self.gen_res.short_id, usertext="delete")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
