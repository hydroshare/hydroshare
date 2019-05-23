import json
import tempfile

from django.core.urlresolvers import reverse
from rest_framework import status

from hs_core.tests.api.rest.base import HSRESTTestCase


class TestResourceFileMetadataEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestResourceFileMetadataEndpoint, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.resources_to_delete = []

    def test_discovery_rest_api(self):
        # Just need to test it works, more thorough tests exist in the discover view
        response = self.client.get(reverse('discover-hsapi', kwargs={}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get("count"), 0)

        # Create resource
        response = self.client.post(reverse('list_create_resource'), {
            'resource_type': 'CompositeResource',
            'title': "File Metadata Test Resource"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = json.loads(response.content)
        res_id = response_json.get("resource_id")
        self.resources_to_delete.append(res_id)

        # matching test
        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?text=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json.get("count"), 1)

        # not matching test
        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?text=Water")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json.get("count"), 1)
