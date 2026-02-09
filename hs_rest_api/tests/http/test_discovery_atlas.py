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


def _full_doc(item):
    """Return the full discovery document from a search result item (post-$lookup)."""
    return (item.get("document") or [{}])[0]


def _year_from_date(value):
    """Extract year from dateCreated (datetime or ISO string)."""
    if value is None:
        return None
    if hasattr(value, "year"):
        return value.year
    s = str(value)
    if len(s) >= 4:
        try:
            return int(s[:4])
        except ValueError:
            pass
    return None


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
            if doc.get("name") in (FIXTURE_NAME_HYDROTOPS, FIXTURE_NAME_MODFLOW):
                creators = list(doc.get("creator") or [])
                creators.append({"type": "Person", "name": cls.test_tag})
                doc["creator"] = creators
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
        term = FIXTURE_TERM_HYDROTOPS
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"term": term, "keyword": self.test_tag, "sortBy": "name", "order": "asc", "pageSize": 50},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_search_returns_results_for_second_fixture_term(self):
        term = FIXTURE_TERM_MODFLOW
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"term": term, "keyword": self.test_tag, "sortBy": "name", "order": "asc", "pageSize": 50},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_MODFLOW, names)

    def test_search_sort_and_pagination(self):
        term = FIXTURE_TERM_HYDROTOPS
        all_resp = self.client.get(
            reverse("discover-hsapi-search"),
            data={"term": term, "keyword": self.test_tag, "sortBy": "name", "order": "asc", "pageSize": 50},
        )
        self.assertEqual(all_resp.status_code, status.HTTP_200_OK)
        all_data = json.loads(all_resp.content.decode())
        all_names = [item.get("name") for item in all_data if item.get("name")]
        expected_page1 = all_names[:5]
        expected_page2 = all_names[5:10]

        page1 = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": term,
                "keyword": self.test_tag,
                "sortBy": "name",
                "order": "asc",
                "pageSize": 5,
                "pageNumber": 1,
            },
        )
        page2 = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": term,
                "keyword": self.test_tag,
                "sortBy": "name",
                "order": "asc",
                "pageSize": 5,
                "pageNumber": 2,
            },
        )
        self.assertEqual(page1.status_code, status.HTTP_200_OK)
        self.assertEqual(page2.status_code, status.HTTP_200_OK)
        data1 = json.loads(page1.content.decode())
        data2 = json.loads(page2.content.decode())
        names1 = [item.get("name") for item in data1 if item.get("name")]
        names2 = [item.get("name") for item in data2 if item.get("name")]
        self.assertEqual(names1, expected_page1)
        self.assertEqual(names2, expected_page2)
        self.assertTrue(set(names1).isdisjoint(set(names2)), "Pagination should not repeat items across pages")

    def test_search_content_type_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": f"{FIXTURE_TERM_HYDROTOPS} {self.test_tag}",
                "keyword": self.test_tag,
                "contentType": "CompositeResource",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data), 0, "Expected at least one result for content-type filter")
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)
        for item in data:
            doc = _full_doc(item)
            is_composite = (
                doc.get("additionalType") == "CompositeResource"
                or "CompositeResource" in (doc.get("content_types") or [])
            )
            self.assertTrue(
                is_composite,
                f"Expected CompositeResource; additionalType={doc.get('additionalType')!r}, "
                f"content_types={doc.get('content_types')!r}",
            )

    def test_search_creator_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": f"{FIXTURE_TERM_HYDROTOPS} {self.test_tag}",
                "keyword": self.test_tag,
                "creatorName": FIXTURE_CREATOR_TOPKAPI,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data), 0, "Expected at least one result for creator filter")
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)
        for item in data:
            creators = item.get("creator") or _full_doc(item).get("creator")
            self.assertIsNotNone(creators, f"Expected creator on document: {item.get('name')!r}")
            creator_names = [c.get("name") for c in creators if c.get("name")]
            self.assertIn(
                FIXTURE_CREATOR_TOPKAPI,
                creator_names,
                f"Expected creator {FIXTURE_CREATOR_TOPKAPI!r} in {creator_names!r}",
            )

    def test_search_keyword_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": self.test_tag,
                "keyword": FIXTURE_KEYWORD_HYDROLOGIC,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data), 0, "Expected at least one result for keyword filter")
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)
        for item in data:
            keywords = item.get("keywords") or _full_doc(item).get("keywords")
            self.assertIsNotNone(keywords, f"Expected keywords on document: {item.get('name')!r}")
            self.assertIn(
                FIXTURE_KEYWORD_HYDROLOGIC,
                keywords,
                f"Expected keyword {FIXTURE_KEYWORD_HYDROLOGIC!r} in {keywords!r}",
            )

    def test_search_provider_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": f"{FIXTURE_TERM_HYDROTOPS} {self.test_tag}",
                "keyword": self.test_tag,
                "providerName": FIXTURE_PROVIDER,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data), 0, "Expected at least one result for provider filter")
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)
        for item in data:
            doc = _full_doc(item)
            provider = doc.get("provider")
            self.assertIsNotNone(provider, f"Expected provider on document: {doc.get('name')!r}")
            provider_name = provider.get("name")
            self.assertEqual(
                provider_name,
                FIXTURE_PROVIDER,
                f"Expected provider {FIXTURE_PROVIDER!r}, got {provider_name!r}",
            )

    def test_search_date_filter(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={
                "term": f"{FIXTURE_TERM_HYDROTOPS} {self.test_tag}",
                "keyword": self.test_tag,
                "dateCreatedStart": FIXTURE_YEAR_CREATED,
                "dateCreatedEnd": FIXTURE_YEAR_CREATED,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertGreater(len(data), 0, "Expected at least one result for date filter")
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)
        for item in data:
            doc = _full_doc(item)
            date_created = doc.get("dateCreated")
            self.assertIsNotNone(date_created, f"Expected dateCreated on document: {doc.get('name')!r}")
            year = _year_from_date(date_created)
            self.assertIsNotNone(year, f"Expected dateCreated year; got {date_created!r}")
            self.assertEqual(
                year,
                FIXTURE_YEAR_CREATED,
                f"Expected dateCreated year {FIXTURE_YEAR_CREATED}, got {year}",
            )

    def test_search_empty_results(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"term": f"xyznonexistent_{uuid.uuid4().hex}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        self.assertEqual(data, [])


class TestDiscoveryAtlasSearchValidation(HSRESTTestCase):
    def test_search_invalid_page_number_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search"), data={"pageNumber": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, pageNumber must be greater than 0", msgs)

    def test_search_invalid_page_size_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search"), data={"pageSize": -1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, pageSize must be greater than 0", msgs)

    def test_search_invalid_date_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"dateCreatedStart": 2020, "dateCreatedEnd": 2019},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateCreatedEnd must be greater or equal to dateCreatedStart", msgs)

    def test_search_invalid_published_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"publishedStart": 2022, "publishedEnd": 2021},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, publishedEnd must be greater or equal to publishedStart", msgs)

    def test_search_invalid_modified_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"dateModifiedStart": 2021, "dateModifiedEnd": 2020},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateModifiedEnd must be greater or equal to dateModifiedStart", msgs)

    def test_search_invalid_data_coverage_range_returns_400(self):
        response = self.client.get(
            reverse("discover-hsapi-search"),
            data={"dataCoverageStart": 2020, "dataCoverageEnd": 2019},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dataCoverageEnd must be greater or equal to dataCoverageStart", msgs)

    def test_search_invalid_year_returns_400(self):
        response = self.client.get(reverse("discover-hsapi-search"), data={"dateCreatedStart": 0})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "Validation error")
        msgs = [d.get("msg", "") for d in data.get("details", [])]
        self.assertIn("Value error, dateCreatedStart is not a valid year", msgs)


class TestDiscoveryAtlasTypeaheadIntegration(AtlasIntegrationBase):
    def test_typeahead_returns_results_for_term(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead"),
            data={"term": f"{FIXTURE_TERM_HYDROTOPS} {self.test_tag}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_typeahead_creator_field(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead"),
            data={"term": self.test_tag, "field": "creator"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_HYDROTOPS, names)

    def test_typeahead_creator_field_valocchi(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead"),
            data={"term": self.test_tag, "field": "creator"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = json.loads(response.content.decode())
        names = {item.get("name") for item in data if item.get("name")}
        self.assertIn(FIXTURE_NAME_MODFLOW, names)

    def test_typeahead_subject_field(self):
        response = self.client.get(
            reverse("discover-hsapi-typeahead"),
            data={"term": f"{FIXTURE_KEYWORD_HYDROLOGIC} {self.test_tag}", "field": "subject"},
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
        response = self.client.get(reverse("discover-hsapi-typeahead"), data={"term": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = json.loads(response.content.decode())
        self.assertEqual(data.get("error"), "term is required")
