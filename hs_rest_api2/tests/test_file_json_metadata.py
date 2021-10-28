import os
import json

from django.core.urlresolvers import reverse
from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare import current_site_url
from hs_core.tests.api.rest.base import HSRESTTestCase


def normalize_metadata(metadata_str, short_id):
    """Prepares metadata string to match resource id and hydroshare url of original"""
    return metadata_str \
        .replace("http://www.hydroshare.org", current_site_url()) \
        .replace("0fdbb27857844644bacc274882601598", short_id)


class TestFileBasedJSON(HSRESTTestCase):

    base_dir = 'hs_rest_api2/tests/data/json/'

    def test_resource_metadata_retrieve(self):
        # Create resource
        res = hydroshare.create_resource(resource_type='CompositeResource',
                                           owner=self.user,
                                           title='triceratops',
                                           metadata=[], )

        # Verify resource exists
        response = self.client.get(reverse('hsapi2:resource_metadata_json', kwargs={"pk": res.short_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())

        with open(os.path.join(self.base_dir, "resource.json"), "r") as f:
            expected = json.loads(normalize_metadata(f.read(), res.short_id))
        expected['modified'] = response_json['modified']
        expected['created'] = response_json['created']
        self.assertEqual(response_json, expected)
