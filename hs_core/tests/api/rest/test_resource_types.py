import json

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase

from hs_core.hydroshare.utils import get_resource_types


class TestResourceTypes(APITestCase):

    def setUp(self):
        self.client = APIClient()

    def test_resource_typelist(self):
        resource_types = set([t.__name__ for t in get_resource_types()])

        response = self.client.get('/hsapi/resourceTypes/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        rest_resource_types = set([t['resource_type'] for t in content])

        self.assertEqual(resource_types, rest_resource_types)