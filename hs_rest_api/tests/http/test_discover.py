import json
import tempfile

from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from unittest import skip

from hs_core.models import BaseResource
from hs_core.tests.api.rest.base import HSRESTTestCase


class TestResourceFileMetadataEndpoint(HSRESTTestCase):
    def setUp(self):
        super(TestResourceFileMetadataEndpoint, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.resources_to_delete = []
        # delete any existing records from haystack
        call_command('clear_index', "--noinput")

    def tearDown(self):
        super(TestResourceFileMetadataEndpoint, self).tearDown()
        # clean up haystack
        call_command('clear_index', "--noinput")

    @skip("TODO: https://github.com/hydroshare/hydroshare/issues/5736")
    def test_discovery_rest_api(self):
        # Just need to test it works, more thorough tests exist in the discover view
        response = self.client.get(reverse('discover-hsapi', kwargs={}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be no resources in the index
        self.assertEqual(response_json.get("count"), 0)

        # create a resource
        response = self.client.post(reverse('list_create_resource'), {
            'resource_type': 'CompositeResource',
            'title': "File Metadata Test Resource"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = json.loads(response.content.decode())
        res_id = response_json.get("resource_id")
        self.resources_to_delete.append(res_id)

        # set the resource to discoverable so that it shows up in the discover view
        resource = BaseResource.objects.get(short_id=res_id)
        resource.raccess.discoverable = True
        resource.raccess.save()

        # matching search test
        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?title__contains=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be one matching resource in the index
        self.assertEqual(response_json.get("count"), 1)

        # not matching search test
        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?title__contains=Water")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be no matching resources in the index
        self.assertEqual(response_json.get("count"), 0)
