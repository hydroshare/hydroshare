import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.urls import reverse

from rest_framework import status

from hs_core import hydroshare
from hs_core.views import get_supported_file_types_for_resource_type


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

    def test_resource_type_supported_file_types(self):
        # here we are testing the get_supported_file_types_for_resource_type view function

        # test for CollectionResource
        resp_json = self._make_request("CollectionResource")
        self.assertEqual(resp_json['file_types'], '[]')

        # test for CompositeResource
        resp_json = self._make_request("CompositeResource")
        self.assertEqual(resp_json['file_types'], '".*"')

        # test for ToolResource
        resp_json = self._make_request("ToolResource")
        self.assertEqual(resp_json['file_types'], '[]')

    def _make_request(self, resource_type):
        url_params = {'resource_type': resource_type}
        url = reverse('resource_type_file_types', kwargs=url_params)
        request = self.factory.post(url, data={})
        request.user = self.john
        # make it a ajax request
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        response = get_supported_file_types_for_resource_type(request,
                                                              resource_type=resource_type)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        resp_json = json.loads(response.content.decode())
        return resp_json
