import json

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse

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

    def test_resource_type_multiple_file_upload(self):
        # here we are testing the is_multiple_file_upload_allowed view function

        # test for generic resource type
        resp_json = self._make_request("GenericResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for NetcdfResource
        resp_json = self._make_request("NetcdfResource")
        self.assertEqual(resp_json['allow_multiple_file'], False)

        # test for TimeSeriesResource
        resp_json = self._make_request("TimeSeriesResource")
        self.assertEqual(resp_json['allow_multiple_file'], False)

        # test for CollectionResource
        resp_json = self._make_request("CollectionResource")
        self.assertEqual(resp_json['allow_multiple_file'], False)

        # test for CompositeResource
        resp_json = self._make_request("CompositeResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for RasterResource
        resp_json = self._make_request("RasterResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for GeographicFeatureResource
        resp_json = self._make_request("GeographicFeatureResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for ModelProgramResource
        resp_json = self._make_request("ModelProgramResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for ModelInstanceResource
        resp_json = self._make_request("ModelInstanceResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for MODFLOWModelInstanceResource
        resp_json = self._make_request("MODFLOWModelInstanceResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for ScriptResource
        resp_json = self._make_request("ScriptResource")
        self.assertEqual(resp_json['allow_multiple_file'], True)

        # test for SWATModelInstanceResource
        resp_json = self._make_request("SWATModelInstanceResource")
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
        resp_json = json.loads(response.content)
        return resp_json
