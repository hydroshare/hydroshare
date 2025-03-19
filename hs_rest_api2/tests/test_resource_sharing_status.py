import json

from rest_framework import status

from hs_core.hydroshare import resource
from hs_core.tests.api.rest.base import HSRESTTestCase


class TestResourceSharingStatus(HSRESTTestCase):
    def setUp(self):
        super(TestResourceSharingStatus, self).setUp()
        self.res = resource.create_resource(
            resource_type='CompositeResource',
            owner=self.user,
            title='Test Resource for testing Sharing Status',
        )
        self.url = "/hsapi2/resource/{}/sharing_status/json/".format(self.res.short_id)

    def test_get_sharing_status(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['sharing_status'], 'private')
        # set the resource to discoverable
        self.res.raccess.discoverable = True
        self.res.raccess.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['sharing_status'], 'discoverable')
        # set the resource to public
        self.res.raccess.public = True
        self.res.raccess.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['sharing_status'], 'public')
        # set the resource to published
        self.res.raccess.published = True
        self.res.raccess.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        self.assertEqual(response_json['sharing_status'], 'published')
