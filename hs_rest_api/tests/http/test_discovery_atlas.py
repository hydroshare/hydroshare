"""
Discovery Atlas search and typeahead API tests.
Currently loading a curated fixture (discovery_atlas_20.json) into Atlas
instead of staging via resource models (create resource → make public → pipeline).

"""
import json
import os
import time
import uuid

from bson import json_util
from bson.objectid import ObjectId
from django.urls import reverse
from rest_framework import status

from hs_core.tests.api.rest.base import HSRESTTestCase


def _get_discovery_atlas():
    from hs_rest_api import discovery_atlas
    return discovery_atlas


# Fixture-derived values for assertions (discovery_atlas_20.json)
FIXTURE_TERM_HYDROTOPS = "HydroTops"
FIXTURE_TERM_MODFLOW = "MODFLOW"
FIXTURE_NAME_HYDROTOPS = "This is terrain files prepared using HydroTops for  sanmarcosterrain"
FIXTURE_NAME_MODFLOW = "Interactive MODFLOW simulation to study impact of pumping on streamflow"
FIXTURE_CREATOR_TOPKAPI = "topkapi app"
FIXTURE_CREATOR_VALOCCHI = "Valocchi"
FIXTURE_KEYWORD_HYDROLOGIC = "Hydrologic modeling"
FIXTURE_YEAR_CREATED = 2017
FIXTURE_PROVIDER = "HydroShare"


class AtlasIntegrationBase(HSRESTTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_tag = f"atlas_fixture_{uuid.uuid4().hex[:12]}"
        discovery_atlas = _get_discovery_atlas()
        cls.collection = discovery_atlas.hydroshare_atlas_db["discovery"]
        cls.collection.database.client.admin.command("ping")
        cls._verify_search_index()
        cls._load_fixture()
        cls._wait_for_fixture_indexing()

    @classmethod
    def tearDownClass(cls):
        try:
            if hasattr(cls, "collection") and hasattr(cls, "test_tag"):
                cls.collection.delete_many({"atlas_test_tag": cls.test_tag})
        finally:
            super().tearDownClass()

    @classmethod
    def _verify_search_index(cls):
        cursor = cls.collection.aggregate([
            {"$listSearchIndexes": {}},
            {"$match": {"name": "fuzzy_search"}},
            {"$limit": 1},
        ])
        if not any(cursor):
            raise RuntimeError("Atlas search index 'fuzzy_search' missing")

    @classmethod
    def _load_fixture(cls):
        fixture_path = os.path.join(
            os.path.dirname(__file__), "..", "fixtures", "discovery_atlas_20.json"
        )
        if not os.path.isfile(fixture_path):
            raise RuntimeError(f"Fixture not found: {fixture_path}")
        with open(fixture_path, "rb") as f:
            raw = f.read().decode("utf-8")
        documents = json_util.loads(raw)
        if not isinstance(documents, list):
            raise RuntimeError("Fixture must be a JSON array of discovery documents")
        for doc in documents:
            doc["_id"] = ObjectId()
            doc["atlas_test_tag"] = cls.test_tag
            keywords = list(doc.get("keywords") or [])
            keywords.append(cls.test_tag)
            doc["keywords"] = keywords
        cls.collection.delete_many({"atlas_test_tag": cls.test_tag})
        cls.collection.insert_many(documents)

    @classmethod
    def _wait_for_fixture_indexing(cls):
        query = cls.test_tag
        for _ in range(60):
            res = list(cls.collection.aggregate([
                {
                    "$search": {
                        "index": "fuzzy_search",
                        "text": {"query": query, "path": ["keywords"]},
                        "returnStoredSource": True,
                    }
                },
                {"$limit": 10},
            ]))
            names = {doc.get("name") for doc in res}
            if FIXTURE_NAME_HYDROTOPS in names:
                return
            time.sleep(1)
        raise RuntimeError(
            f"Fixture not searchable in Atlas within 60s (searched for tag {query!r})"
        )


class TestDiscoveryAtlasSearchIntegration(AtlasIntegrationBase):
    def test_search_returns_results_for_fixture_term(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&sortBy=name&order=asc&pageSize=10"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_returns_results_for_second_fixture_term(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_MODFLOW}&sortBy=name&order=asc&pageSize=10"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_MODFLOW, names)

    def test_search_sort_and_pagination(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&sortBy=name&order=asc&pageSize=5&pageNumber=1"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)
        self.assertLessEqual(len(data), 5)
        names = [item.get("name") for item in data if item.get("name")]
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names, "Expected fixture doc in sorted results")
        if len(names) >= 2:
            self.assertEqual(names, sorted(names), "Results with names should be sorted by name ascending")

    def test_search_content_type_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&contentType=CompositeResource"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_creator_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&creatorName={FIXTURE_CREATOR_TOPKAPI.replace(' ', '%20')}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_keyword_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&keyword={FIXTURE_KEYWORD_HYDROLOGIC.replace(' ', '%20')}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_provider_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}&providerName={FIXTURE_PROVIDER}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_date_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={FIXTURE_TERM_HYDROTOPS}"
              f"&dateCreatedStart={FIXTURE_YEAR_CREATED}"
              f"&dateCreatedEnd={FIXTURE_YEAR_CREATED}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_empty_results(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + "?term=xyznonexistent_fixture_term_12345"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertEqual(data, [])


class TestDiscoveryAtlasSearchValidation(HSRESTTestCase):
    def test_search_invalid_page_number_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageNumber=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, pageNumber must be greater than 0", msgs)

    def test_search_invalid_page_size_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageSize=-1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, pageSize must be greater than 0", msgs)

    def test_search_invalid_date_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + "?dateCreatedStart=2020&dateCreatedEnd=2019"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateCreatedEnd must be greater or equal to dateCreatedStart", msgs)

    def test_search_invalid_published_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + "?publishedStart=2022&publishedEnd=2021"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, publishedEnd must be greater or equal to publishedStart", msgs)

    def test_search_invalid_modified_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + "?dateModifiedStart=2021&dateModifiedEnd=2020"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateModifiedEnd must be greater or equal to dateModifiedStart", msgs)

    def test_search_invalid_data_coverage_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + "?dataCoverageStart=2020&dataCoverageEnd=2019"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dataCoverageEnd must be greater or equal to dataCoverageStart", msgs)

    def test_search_invalid_year_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?dateCreatedStart=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateCreatedStart is not a valid year", msgs)


class TestDiscoveryAtlasTypeaheadIntegration(AtlasIntegrationBase):
    def test_typeahead_returns_results_for_term(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + f"?term={FIXTURE_TERM_HYDROTOPS}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_typeahead_creator_field(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=topkapi&field=creator"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_typeahead_creator_field_valocchi(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + "?term=Valocchi&field=creator"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_MODFLOW, names)

    def test_typeahead_subject_field(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead") + f"?term={FIXTURE_KEYWORD_HYDROLOGIC}&field=subject"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)


class TestDiscoveryAtlasTypeaheadValidation(HSRESTTestCase):
    def test_typeahead_missing_term_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-typeahead"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "term is required")

    def test_typeahead_empty_term_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-typeahead") + "?term=")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "term is required")
