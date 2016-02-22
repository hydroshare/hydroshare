import json

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase


class TestResourceTypes(APITestCase):

    def setUp(self):
        self.client = APIClient()

        # Use a static list so that this test breaks when a resource type is
        # added or removed (so that the test can be updated)
        self.resource_types = {'GenericResource',
                               'RasterResource',
                               'RefTimeSeriesResource',
                               'TimeSeriesResource',
                               'NetcdfResource',
                               'ModelProgramResource',
                               'ModelInstanceResource',
                               'ToolResource',
                               'SWATModelInstanceResource',
                               'GeographicFeatureResource',
                               'ScriptResource'}

    def test_resource_typelist(self):
        response = self.client.get('/hsapi/resourceTypes/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        rest_resource_types = set([t['resource_type'] for t in content])

        self.assertEqual(self.resource_types, rest_resource_types)
