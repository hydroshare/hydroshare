import json

from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.test import APITestCase


class TestContentTypes(APITestCase):

    def setUp(self):
        self.client = APIClient()

        self.content_types = {'GenericLogicalFile',
                               'GeoRasterLogicalFile',
                               'NetCDFLogicalFile',
                               'GeoFeatureLogicalFile',
                               'RefTimeseriesLogicalFile',
                               'TimeSeriesLogicalFile',
                               'FileSetLogicalFile'}

    def test_content_typelist(self):
        response = self.client.get('/hsapi/resource/content_types/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        rest_content_types = set([t['content_type'] for t in content])

        self.assertEqual(self.content_types, rest_content_types)
