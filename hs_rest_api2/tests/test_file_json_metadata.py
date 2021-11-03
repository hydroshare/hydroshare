import os
import json

from django.core.urlresolvers import reverse
from hsmodels.schemas.resource import ResourceMetadataIn
from rest_framework import status

from hs_core import hydroshare
from hs_core.hydroshare import current_site_url
from hs_core.tests.api.rest.base import HSRESTTestCase


def normalize_metadata(metadata_str, short_id):
    """Prepares metadata string to match resource id and hydroshare url of original"""
    return metadata_str \
        .replace("http://www.hydroshare.org", current_site_url()) \
        .replace("0fdbb27857844644bacc274882601598", short_id)


def sorting(item):
    if isinstance(item, dict):
        return sorted((key, sorting(values)) for key, values in item.items())
    if isinstance(item, list):
        return sorted(sorting(x) for x in item)
    else:
        return item


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

    def test_resource_metadata_update(self):
        # Create resource
        res = hydroshare.create_resource(resource_type='CompositeResource',
                                           owner=self.user,
                                           title='triceratops',
                                           metadata=[], )

        # Verify resource exists
        response = self.client.get(reverse('hsapi2:resource_metadata_json', kwargs={"pk": res.short_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with open(os.path.join(self.base_dir, "full_resource.json"), "r") as f:
            full_resource_json = json.loads(normalize_metadata(f.read(), res.short_id))
        full_resource_json_in = ResourceMetadataIn(**full_resource_json)
        in_resource_json = full_resource_json_in.json(exclude_defaults=True)
        self.client.put(reverse('hsapi2:resource_metadata_json', kwargs={"pk": res.short_id}),
                        data=in_resource_json, format="json")

        response = self.client.get(reverse('hsapi2:resource_metadata_json', kwargs={"pk": res.short_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = json.loads(response.content.decode())
        full_resource_json['modified'] = response_json['modified']
        full_resource_json['created'] = response_json['created']
        self.assertEqual(sorting(response_json), sorting(full_resource_json))