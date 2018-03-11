import os
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

    def test_metadata_update_retrieve(self):
        # Test 404
        response = self.client.get(reverse('get_update_resource_file_metadata', kwargs={
            "pk": "abc123",
            "file_id": 1234
        }))
        self.assertEqual(response.content,
                         '{"detail":"No resource was found for resource id:abc123"}')

        # Create resource
        response = self.client.post(reverse('list_create_resource'), {
            'resource_type': 'CompositeResource',
            'title': "File Metadata Test Resource"
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = json.loads(response.content)
        res_id = response_json.get("resource_id")
        self.resources_to_delete.append(res_id)

        # Verify resource exists
        response = self.client.get(reverse('get_update_delete_resource', kwargs={"pk": res_id}))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

        response = self.client.get(reverse('list_create_resource_file', kwargs={"pk": res_id}))
        response_json = json.loads(response.content)
        self.assertEqual(response_json.get("results"), [])

        # Create new resource file
        txt_file_name = 'text2.txt'
        txt_file_path = os.path.join(self.temp_dir, txt_file_name)
        txt = open(txt_file_path, 'w')
        txt.write("Hello World, again.\n")
        txt.close()
        response = self.client.post(reverse('list_create_resource_file', kwargs={"pk": res_id}),
                                    {'file': (txt_file_name,
                                              open(txt_file_path),
                                              'text/plain')})

        response = self.client.get(reverse('list_create_resource_file', kwargs={"pk": res_id}))
        response_json = json.loads(response.content)
        self.assertEqual(len(response_json.get("results")), 1)
        file_id = response_json.get("results")[0]['id']

        # Test Empty Metadata
        file_metadata_url = reverse('get_update_resource_file_metadata', kwargs={
            "pk": res_id,
            "file_id": file_id
        })
        response = self.client.get(file_metadata_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Update title
        response = self.client.put(file_metadata_url, {
            "title": "New Metadata Title"
        }, format="json")
        response = self.client.get(file_metadata_url)
        json_response = json.loads(response.content)
        self.assertEqual(json_response.get("title"), "New Metadata Title")

        # Update keywords
        response = self.client.put(file_metadata_url, {
            "keywords": [u"keyword1", u"keyword2"]
        }, format="json")
        response = self.client.get(file_metadata_url)
        json_response = json.loads(response.content)
        self.assertEqual(json_response.get("keywords"), [u"keyword1", u"keyword2"])

        # Update keywords
        response = self.client.put(file_metadata_url, {
            "extra_metadata": {
                "this": "is",
                "a": "test"
            }
        }, format="json")
        response = self.client.get(file_metadata_url)
        json_response = json.loads(response.content)
        self.assertEqual(json_response.get("extra_metadata"), {u'a': u'test', u'this': u'is'})

        # Update spatial coverage
        response = self.client.put(file_metadata_url, {
            "spatial_coverage":  {
                "units": "Decimal degrees",
                "east": -84.0465,
                "north": 49.6791,
                "name": "12232",
                "projection": "WGS 84 EPSG:4326"
            },
        }, format="json")
        response = self.client.get(file_metadata_url)
        json_response = json.loads(response.content)
        self.assertEqual(json_response.get("spatial_coverage"), {
            u'units': u'Decimal degrees',
            u'east': -84.0465,
            u'north': 49.6791,
            u'name': u'12232',
            u'projection': u'WGS 84 EPSG:4326'
        })

        # Update temporal coverage
        response = self.client.put(file_metadata_url, {
            "temporal_coverage": {
                "start": "2018-02-04",
                "end": "2018-02-06"
            }
        }, format="json")
        response = self.client.get(file_metadata_url)
        json_response = json.loads(response.content)
        self.assertEqual(json_response.get("temporal_coverage"), {
            "start": "2018-02-04",
            "end": "2018-02-06"
        })
