import json
import tempfile

from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from unittest import skip

from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_core import hydroshare


class TestDiscoverResourceDelete(HSRESTTestCase):
    def setUp(self):
        super(TestDiscoverResourceDelete, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.resources_to_delete = []
        # delete any existing records from haystack
        call_command('clear_index', "--noinput")

        self.admin = hydroshare.create_account(
            'admin@gmail.com',
            username='admin',
            first_name='admin',
            last_name='admin',
            superuser=True,
            groups=[]
        )

        self.owner = hydroshare.create_account(
            'owner@gmail.com',
            username='owner',
            first_name='owner',
            last_name='owner',
            superuser=False,
            groups=[]
        )

    def tearDown(self):
        super(TestDiscoverResourceDelete, self).tearDown()
        # clean up haystack
        call_command('clear_index', "--noinput")

    @skip("TODO: https://github.com/hydroshare/hydroshare/issues/5736")
    def test_discover_res_delete(self):
        """Test that deleting user account cascades to remove resource from solr index
        """
        response = self.client.get(reverse('discover-hsapi', kwargs={}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be no resources in the index
        self.assertEqual(response_json.get("count"), 0)

        resource = hydroshare.create_resource(
            resource_type='CompositeResource',
            owner=self.owner,
            title='Test Resource',
            metadata=[],
        )

        # set the resource to discoverable so that it shows up in the discover view
        resource.raccess.discoverable = True
        resource.raccess.save()

        response = self.client.get(reverse('discover-hsapi', kwargs={}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be 1 resource in the index
        self.assertEqual(response_json.get("count"), 1)

        # matching search test
        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?title__contains=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be one matching resource in the index
        self.assertEqual(response_json.get("count"), 1)

        # delete_resource(resource.short_id)
        self.owner.delete()

        response = self.client.get(reverse('discover-hsapi', kwargs={}) + "?title__contains=Test")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        # there should be no matching resources in the index
        self.assertEqual(response_json.get("count"), 0)
