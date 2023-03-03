import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group, User
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import is_multiple_file_upload_allowed


class TestResourceTypeFileTypes(TestCase):

    def setUp(self):
        super(TestResourceTypeFileTypes, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.username = 'john'
        self.password = 'jhmypassword'
        self.john = hydroshare.create_account(
            'john@gmail.com',
            username=self.username,
            first_name='John',
            last_name='Clarson',
            superuser=False,
            password=self.password,
            groups=[]
        )

        self.factory = RequestFactory()

    def tearDown(self):
        super(TestResourceTypeFileTypes, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()

    def test_resource_type_multiple_file_upload(self):
        # here we are testing the is_multiple_file_upload_allowed view function

        # test for CollectionResource
        resp_json = self._make_request("CollectionResource")
        self.assertEqual(resp_json['allow_multiple_file'], False)

        # test for CompositeResource
        resp_json = self._make_request("CompositeResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for ToolResource
        resp_json = self._make_request("ToolResource")
        self.assertEqual(resp_json['allow_multiple_file'], False)

    def _make_request(self, resource_type):
        url_params = {'resource_type': resource_type}
        url = reverse('resource_type_multiple_file_upload', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.john
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = is_multiple_file_upload_allowed(request, resource_type=resource_type)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content.decode())
        return resp_json
