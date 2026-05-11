from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from pymongo.errors import PyMongoError


class DiscoveryAtlasTypeaheadEndpointTests(TestCase):
    @patch("hs_rest_api.discovery_atlas.AtlasSearchService.typeahead")
    def test_typeahead_endpoint_uses_default_term_field(self, mock_typeahead):
        mock_typeahead.return_value = [{"name": "Water"}]
        response = self.client.get(reverse("discover-hsapi-typeahead"), {"term": "wat"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, [{"name": "Water"}])
        mock_typeahead.assert_called_once_with(term="wat", field="term")

    @patch("hs_rest_api.discovery_atlas.AtlasSearchService.typeahead")
    def test_typeahead_endpoint_passes_creator_field(self, mock_typeahead):
        mock_typeahead.return_value = []
        response = self.client.get(reverse("discover-hsapi-typeahead"), {"term": "jane", "field": "creator"})
        self.assertEqual(response.status_code, 200)
        mock_typeahead.assert_called_once_with(term="jane", field="creator")

    @patch("hs_rest_api.discovery_atlas.AtlasSearchService.typeahead")
    def test_typeahead_endpoint_passes_subject_field(self, mock_typeahead):
        mock_typeahead.return_value = []
        response = self.client.get(reverse("discover-hsapi-typeahead"), {"term": "snow", "field": "subject"})
        self.assertEqual(response.status_code, 200)
        mock_typeahead.assert_called_once_with(term="snow", field="subject")

    @patch("hs_rest_api.discovery_atlas.AtlasSearchService.typeahead")
    def test_typeahead_endpoint_passes_funder_field(self, mock_typeahead):
        mock_typeahead.return_value = []
        response = self.client.get(reverse("discover-hsapi-typeahead"), {"term": "nsf", "field": "funder"})
        self.assertEqual(response.status_code, 200)
        mock_typeahead.assert_called_once_with(term="nsf", field="funder")

    @patch("hs_rest_api.discovery_atlas.AtlasSearchService.typeahead")
    def test_typeahead_endpoint_returns_503_on_pymongo_error(self, mock_typeahead):
        mock_typeahead.side_effect = PyMongoError("mongo down")
        response = self.client.get(reverse("discover-hsapi-typeahead"), {"term": "wat"})
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(
            response.content,
            {"message": "Discovery Atlas typeahead unavailable: mongo down"},
        )
