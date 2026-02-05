"""
Tests for Discovery Atlas search and typeahead API endpoints.

Integration tests hit the real Atlas instance (when available) with staged data.
"""
import json
import time
import uuid
from datetime import datetime

from bson.objectid import ObjectId
from django.urls import reverse
from rest_framework import status

from hs_core.tests.api.rest.base import HSRESTTestCase
from hs_rest_api import discovery_atlas


class AtlasIntegrationBase(HSRESTTestCase):
    """Seeds a few documents into the local Atlas discovery collection for tests."""

    __test__ = False
    seed_tag = f"atlas_integration_seed_{uuid.uuid4().hex}"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.seed_token = f"atlas_seed_{uuid.uuid4().hex[:8]}"
        cls.alpha_name = f"AtlasSeed Alpha Water {cls.seed_token}"
        cls.beta_name = f"AtlasSeed Beta Snow {cls.seed_token}"
        cls.zulu_name = f"AtlasSeed Zulu Climate {cls.seed_token}"
        cls.collection = discovery_atlas.hydroshare_atlas_db["discovery"]
        cls.collection.database.client.admin.command("ping")
        cls._verify_search_index()
        cls._seed_documents()
        cls._wait_for_seed_indexing()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.collection.delete_many({"test_tag": cls.seed_tag})
        finally:
            super().tearDownClass()

    @classmethod
    def _verify_search_index(cls):
        cursor = cls.collection.aggregate([
            {"$listSearchIndexes": {}},
            {"$match": {"name": "fuzzy_search"}},
            {"$limit": 1},
        ])
        exists = any(cursor)
        if not exists:
            raise RuntimeError("Atlas search index 'fuzzy_search' missing")

    @classmethod
    def _seed_documents(cls):
        cls.collection.delete_many({"test_tag": cls.seed_tag})
        documents = [
            {
                "_id": ObjectId(),
                "name": cls.alpha_name,
                "description": "atlas_seed hydrology water dataset for river analysis",
                "keywords": [cls.seed_token, "atlas_seed_water", "hydrology", "river", "dataset"],
                "creator": [{"name": "Alice Seed"}],
                "first_creator": {"name": "Alice Seed"},
                "contributor": [{"name": "Bob Seed"}],
                "provider": {"name": "AtlasSeedProvider"},
                "type": "ScientificDataset",
                "additionalType": "CompositeResource",
                "content_types": ["CompositeResource"],
                "dateCreated": datetime(2021, 6, 1),
                "dateModified": datetime(2023, 1, 1),
                "datePublished": datetime(2022, 5, 1),
                "temporalCoverage": {"startDate": datetime(2005, 1, 1), "endDate": datetime(2006, 1, 1)},
                "creativeWorkStatus": "Published",
                "funding": {"name": "AtlasSeed River Grant", "funder": {"name": "AtlasSeedNSF"}},
                "hasPart": [{"name": "AtlasSeed Part A"}],
                "isPartOf": {"name": "AtlasSeed Project River"},
                "associatedMedia": [{"name": "AtlasSeed Photo"}],
                "test_tag": cls.seed_tag,
            },
            {
                "_id": ObjectId(),
                "name": cls.beta_name,
                "description": "atlas_seed snow and ice observations dataset",
                "keywords": [cls.seed_token, "atlas_seed_snow", "snow", "dataset"],
                "creator": [{"name": "Alice Seed"}],
                "first_creator": {"name": "Alice Seed"},
                "contributor": [],
                "provider": {"name": "AtlasSeedProvider"},
                "type": "ScientificDataset",
                "additionalType": "CompositeResource",
                "content_types": ["CompositeResource"],
                "dateCreated": datetime(2023, 5, 1),
                "dateModified": datetime(2024, 1, 1),
                "datePublished": datetime(2023, 6, 1),
                "temporalCoverage": {"startDate": datetime(2015, 1, 1), "endDate": datetime(2016, 1, 1)},
                "creativeWorkStatus": "Published",
                "funding": {"name": "AtlasSeed Snow Grant", "funder": {"name": "AtlasSeedDOE"}},
                "test_tag": cls.seed_tag,
            },
            {
                "_id": ObjectId(),
                "name": cls.zulu_name,
                "description": "atlas_seed climate data NetCDF sample",
                "keywords": [cls.seed_token, "atlas_seed_climate", "climate", "dataset"],
                "creator": [{"name": "Carol Seed"}],
                "first_creator": {"name": "Carol Seed"},
                "contributor": [],
                "provider": {"name": "AtlasSeedProvider"},
                "type": "ScientificDataset",
                "additionalType": "NetcdfResource",
                "content_types": ["NetcdfResource"],
                "dateCreated": datetime(2018, 1, 1),
                "dateModified": datetime(2019, 1, 1),
                "datePublished": datetime(2019, 6, 1),
                "temporalCoverage": {"startDate": datetime(2010, 1, 1), "endDate": datetime(2011, 1, 1)},
                "creativeWorkStatus": "Draft",
                "funding": {"name": "AtlasSeed Climate Grant", "funder": {"name": "AtlasSeedNOAA"}},
                "test_tag": cls.seed_tag,
            },
        ]
        cls.collection.insert_many(documents)

    @classmethod
    def _wait_for_seed_indexing(cls):
        """Wait briefly for seeded docs to be indexed; proceed even if not confirmed."""
        targets = {cls.alpha_name, cls.beta_name, cls.zulu_name}
        if cls.collection.count_documents({"test_tag": cls.seed_tag}) < len(targets):
            raise RuntimeError("Seed documents not found in collection after insert")

        for _ in range(60):
            try:
                res = list(cls.collection.aggregate([
                    {
                        "$search": {
                            "index": "fuzzy_search",
                            "query": {"text": {"path": ["name", "keywords"], "query": cls.seed_token}},
                            "returnStoredSource": True,
                        }
                    },
                    {"$limit": 10},
                ]))
                names = {doc.get("name") for doc in res}
                if targets.issubset(names):
                    return
            except Exception:
                pass
            time.sleep(1)


class TestDiscoveryAtlasSearchIntegration(AtlasIntegrationBase):
    """Calls the real search endpoint using staged Atlas data."""

    def test_search_returns_water_doc(self):
        response = self.client.get(
            reverse("discover-hsapi-search") + f"?term={self.seed_token}&sortBy=name&order=asc&pageSize=5"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item["name"] for item in data}
        self.assertIn(self.alpha_name, names)

    def test_search_sort_by_name_and_pagination(self):
        base_params = (
            f"?term={self.seed_token}"
            f"&keyword={self.seed_token}"
            "&providerName=AtlasSeedProvider&sortBy=name&order=asc"
        )

        page1 = self.client.get(reverse("discover-hsapi-search") + base_params + "&pageSize=2&pageNumber=1")
        page2 = self.client.get(reverse("discover-hsapi-search") + base_params + "&pageSize=2&pageNumber=2")

        self.assertEqual(page1.status_code, status.HTTP_200_OK)
        self.assertEqual(page2.status_code, status.HTTP_200_OK)

        data1 = json.loads(page1.content.decode())
        data2 = json.loads(page2.content.decode())

        names1 = {item["name"] for item in data1}
        names2 = {item["name"] for item in data2}

        self.assertTrue(names1.isdisjoint(names2))
        self.assertSetEqual(names1 | names2, {self.alpha_name, self.beta_name, self.zulu_name})

    def test_search_content_type_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?keyword={self.seed_token}"
              "&contentType=NetcdfResource"
              "&providerName=AtlasSeedProvider"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], self.zulu_name)

    def test_search_creator_keyword_provider_filters(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={self.seed_token}"
              "&creatorName=Alice%20Seed"
              "&providerName=AtlasSeedProvider"
              "&keyword=hydrology"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item["name"] for item in data}
        self.assertIn(self.alpha_name, names)

    def test_search_date_filters(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={self.seed_token}&dateCreatedStart=2020&dateCreatedEnd=2022"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item["name"] for item in data}
        self.assertSetEqual(names, {self.alpha_name})

    def test_search_creative_work_status_filter(self):
        base = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={self.seed_token}"
              f"&keyword={self.seed_token}"
              "&providerName=AtlasSeedProvider"
              "&contentType=CompositeResource"
        )
        self.assertEqual(base.status_code, status.HTTP_200_OK)
        base_names = {item["name"] for item in json.loads(base.content.decode())}
        self.assertTrue({self.alpha_name, self.beta_name}.issubset(base_names))

        response = self.client.get(
            reverse("discover-hsapi-search")
            + f"?term={self.seed_token}&keyword={self.seed_token}&providerName=AtlasSeedProvider"
              "&contentType=CompositeResource&creativeWorkStatus=Published"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item["name"] for item in data}
        if names:
            self.assertSetEqual(names, {self.alpha_name, self.beta_name})
        else:
            self.assertEqual(data, [])

    def test_search_empty_results(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?term=atlas_seed_no_such_term")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertEqual(data, [])


class TestDiscoveryAtlasSearchValidation(HSRESTTestCase):
    """Validation-only cases; DB is not required."""

    def test_search_invalid_page_number_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageNumber=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("pageNumber must be greater than 0" in msg for msg in msgs))

    def test_search_invalid_page_size_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?pageSize=-1")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("pageSize must be greater than 0" in msg for msg in msgs))

    def test_search_invalid_date_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dateCreatedStart=2020&dateCreatedEnd=2019"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("dateCreatedEnd must be greater or equal to dateCreatedStart" in msg for msg in msgs))

    def test_search_invalid_published_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?publishedStart=2022&publishedEnd=2021"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("publishedEnd must be greater or equal to publishedStart" in msg for msg in msgs))

    def test_search_invalid_modified_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dateModifiedStart=2021&dateModifiedEnd=2020"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("dateModifiedEnd must be greater or equal to dateModifiedStart" in msg for msg in msgs))

    def test_search_invalid_data_coverage_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search")
            + "?dataCoverageStart=2020&dataCoverageEnd=2019"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("dataCoverageEnd must be greater or equal to dataCoverageStart" in msg for msg in msgs))

    def test_search_invalid_year_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search") + "?dateCreatedStart=0")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg") for d in data.get("details", [])]
        self.assertTrue(any("dateCreatedStart is not a valid year" in msg for msg in msgs))


class TestDiscoveryAtlasTypeaheadIntegration(AtlasIntegrationBase):
    """Calls the real typeahead endpoint using staged Atlas data."""

    def test_typeahead_returns_water_dataset(self):
        response = self.client.get(reverse("discover-hsapi-typeahead") + f"?term={self.seed_token}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if "name" in item}
        self.assertIn(self.alpha_name, names)

    def test_typeahead_creator_field(self):
        response = self.client.get(reverse("discover-hsapi-typeahead") + "?term=alice seed&field=creator")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if "name" in item}
        self.assertTrue({self.alpha_name, self.beta_name} & names)

    def test_typeahead_subject_field(self):
        response = self.client.get(reverse("discover-hsapi-typeahead") + f"?term={self.seed_token}&field=subject")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if "name" in item}
        self.assertIn(self.zulu_name, names)

    def test_typeahead_funder_field(self):
        response = self.client.get(reverse("discover-hsapi-typeahead") + "?term=AtlasSeedNSF&field=funder")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if "name" in item}
        self.assertIn(self.alpha_name, names)


class TestDiscoveryAtlasTypeaheadValidation(HSRESTTestCase):
    """Validation-only typeahead cases."""

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
