"""
Unit tests for Discovery Atlas search and typeahead API endpoints (issue #6196).
Mocks MongoDB so tests run without a local Atlas container.
Covers the many available query parameters for full coverage.
"""
import json
from unittest.mock import MagicMock, patch

from django.urls import reverse
from rest_framework import status

from hs_core.tests.api.rest.base import HSRESTTestCase


def make_mock_aggregate(return_list):
    """Mock that mimics collection.aggregate(stages).to_list(None)."""
    mock_cursor = MagicMock()
    mock_cursor.to_list.return_value = return_list
    mock_coll = MagicMock()
    mock_coll.aggregate.return_value = mock_cursor
    return mock_coll


@patch("hs_rest_api.discovery_atlas.hydroshare_atlas_db")
class TestDiscoveryAtlasSearch(HSRESTTestCase):
    """Tests for GET /hsapi/discovery-atlas/search and all query parameters."""

    def test_search_empty_results(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(reverse("discover-hsapi-search"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode()), [])

    def test_search_happy_path_returns_list(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([
            {"_id": "abc", "name": "Test Resource", "document": [{"@type": "Dataset"}]}
        ])
        response = self.client.get(reverse("discover-hsapi-search"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Test Resource")

    def test_search_with_term(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([
            {"_id": "xyz", "name": "Water Data", "document": []}
        ])
        response = self.client.get(reverse("discover-hsapi-search") + "?term=water")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Water Data")

    def test_search_with_sort_by_and_order(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        for sort_by in ("name", "dateCreated", "lastModified", "creatorName"):
            response = self.client.get(
                reverse("discover-hsapi-search") + f"?sortBy={sort_by}&order=asc"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, f"sortBy={sort_by}")
        response = self.client.get(
            reverse("discover-hsapi-search") + "?sortBy=name&order=desc"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_pagination(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?pageNumber=2&pageSize=10"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_content_type_filter(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?contentType=CompositeResource"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse("discover-hsapi-search") + "?contentType=CompositeResource&contentType=NetcdfResource"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_creator_name(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?creatorName=Smith"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_keyword(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?keyword=hydrology"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_provider_name(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?providerName=CUAHSI"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_date_filters(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dateCreatedStart=2020&dateCreatedEnd=2024"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?publishedStart=2019&publishedEnd=2023"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dateModifiedStart=2021&dateModifiedEnd=2024"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dataCoverageStart=2000&dataCoverageEnd=2020"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_with_creative_work_status(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-search") + "?creativeWorkStatus=Published"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_invalid_page_number_returns_400(self, mock_db):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageNumber=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertIn("error", data)
        self.assertIn("Validation error", data.get("error", ""))

    def test_search_invalid_page_size_returns_400(self, mock_db):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageSize=-1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_search_invalid_date_range_returns_400(self, mock_db):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dateCreatedStart=2020&dateCreatedEnd=2019"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertIn("error", data)

    def test_search_invalid_year_returns_400(self, mock_db):
        # Use an integer that is not a valid year (datetime rejects year 0)
        response = self.client.get(
            reverse("discover-hsapi-search") + "?dateCreatedStart=0"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@patch("hs_rest_api.discovery_atlas.hydroshare_atlas_db")
class TestDiscoveryAtlasTypeahead(HSRESTTestCase):
    """Tests for GET /hsapi/discovery-atlas/typeahead and query parameters."""

    def test_typeahead_empty_results(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=foo"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode()), [])

    def test_typeahead_happy_path_returns_list(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([
            {"name": "Sample", "keywords": ["water"], "document": []}
        ])
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=water"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Sample")

    def test_typeahead_missing_term_returns_400(self, mock_db):
        response = self.client.get(reverse("discover-hsapi-typeahead"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertIn("error", data)
        self.assertIn("term", data.get("error", "").lower())

    def test_typeahead_field_creator(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=smith&field=creator"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_typeahead_field_subject(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=water&field=subject"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_typeahead_field_funder(self, mock_db):
        mock_db.__getitem__.return_value = make_mock_aggregate([])
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=NSF&field=funder"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
