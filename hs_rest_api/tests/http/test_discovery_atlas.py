import json
from unittest.mock import patch

from unittest_parametrize import ParametrizedTestCase, parametrize, param

from datetime import datetime

from django.conf import settings
from django.test import SimpleTestCase
from pydantic import ValidationError
from rest_framework import status
from rest_framework.test import APIRequestFactory

from hs_rest_api.discovery_atlas import SearchQuery, search as discovery_atlas_search


class TestSearchQuery(ParametrizedTestCase):

    @parametrize(
        "query_params,expected_error",
        [
            param(
                {"paginationToken": None, "dataCoverageStart": "10000"},
                "dataCoverageStart is not a valid year",
                id="invalid_data_coverage_start_year",
            ),
            param(
                {"paginationToken": None, "publishedStart": 2024, "publishedEnd": 2023},
                "publishedEnd must be greater or equal to publishedStart",
                id="invalid_published_date_range",
            ),
            param(
                {"paginationToken": None, "pageNumber": 0},
                "pageNumber must be greater than 0",
                id="invalid_page_number",
            ),
            param(
                {"paginationToken": None, "pageSize": 0},
                "pageSize must be greater than 0",
                id="invalid_page_size",
            ),
        ],
    )
    def test_invalid_query_params(self, query_params, expected_error):
        with self.assertRaises(ValidationError) as context:
            SearchQuery(**query_params)

        self.assertIn(expected_error, str(context.exception))

    def test_stages_with_multiple_query_params(self):
        term = "floodplain"
        keyword = "water velocity"
        creator_name = "Bilbo Baggins"
        content_type = "Notebook"
        creative_work_status = "Published"
        data_coverage_start = 2020
        data_coverage_end = 2025
        funding_funder_name = "NSF"
        sort_by = "dateCreated"
        order = "desc"

        search_query = SearchQuery(
            term=term,
            keyword=keyword,
            creatorName=creator_name,
            contentType=[content_type],
            creativeWorkStatus=[creative_work_status],
            dataCoverageStart=data_coverage_start,
            dataCoverageEnd=data_coverage_end,
            fundingFunderName=funding_funder_name,
            sortBy=sort_by,
            order=order,
            paginationToken=None,
        )

        stages = search_query.stages

        self.assertEqual(len(stages), 3)

        expected_filter = [
            {"compound": {"mustNot": [{"equals": {"path": "dateCreated", "value": None}}]}},
            {
                "range": {
                    "path": "temporalCoverage.startDate",
                    "gte": datetime(data_coverage_start, 1, 1),
                }
            },
            {
                "range": {
                    "path": "temporalCoverage.endDate",
                    "lt": datetime(data_coverage_end + 1, 1, 1),
                }
            },
            {"term": {"path": "type", "query": "ScientificDataset"}},
        ]
        expected_must = [
            {
                "compound": {
                    "should": [
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "name",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_NAME}},
                            }
                        },
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "description",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_DESCRIPTION}},
                            }
                        },
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "keywords",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_KEYWORDS}},
                            }
                        },
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "creator.name",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_CREATOR_NAME}},
                            }
                        },
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "first_creator.name",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_FIRST_CREATOR_NAME}},
                            }
                        },
                        {
                            "autocomplete": {
                                "query": term,
                                "path": "contributor.name",
                                "fuzzy": {"maxEdits": 1},
                                "score": {"boost": {"value": settings.SEARCH_BOOST_CONTRIBUTOR_NAME}},
                            }
                        },
                    ]
                }
            },
            {
                "compound": {
                    "should": [
                        {"term": {"path": "additionalType", "query": content_type}},
                        {"term": {"path": "content_types", "query": content_type}},
                    ]
                }
            },
            {
                "text": {
                    "path": ["creator.name", "contributor.name"],
                    "query": creator_name,
                }
            },
            {"text": {"path": "keywords", "query": keyword}},
            {
                "text": {"path": "funding.funder.name", "query": funding_funder_name}
            },
            {
                "compound": {
                    "should": [
                        {"term": {"path": "creativeWorkStatus", "query": creative_work_status}},
                        {"term": {"path": "creativeWorkStatus.name", "query": creative_work_status}},
                    ]
                }
            },
        ]
        expected_should = [
            {
                "autocomplete": {
                    "query": creator_name,
                    "path": "creator.name",
                    "fuzzy": {"maxEdits": 1},
                    "score": {"boost": {"value": settings.SEARCH_BOOST_CREATOR_NAME_FILTER}},
                }
            },
            {
                "autocomplete": {
                    "query": creator_name,
                    "path": "first_creator.name",
                    "fuzzy": {"maxEdits": 1},
                    "score": {"boost": {"value": settings.SEARCH_BOOST_FIRST_CREATOR_NAME_FILTER}},
                }
            },
            {
                "autocomplete": {
                    "query": creator_name,
                    "path": "contributor.name",
                    "fuzzy": {"maxEdits": 1},
                    "score": {"boost": {"value": settings.SEARCH_BOOST_CONTRIBUTOR_NAME_FILTER}},
                }
            },
            {
                "autocomplete": {
                    "query": keyword,
                    "path": "keywords",
                    "fuzzy": {"maxEdits": 1},
                    "score": {"boost": {"value": settings.SEARCH_BOOST_KEYWORD_FILTER}},
                }
            },
            {
                "autocomplete": {
                    "query": funding_funder_name,
                    "path": "funding.funder.name",
                    "fuzzy": {"maxEdits": 1},
                    "score": {"boost": {"value": settings.SEARCH_BOOST_FUNDING_FUNDER_NAME_FILTER}},
                }
            },
            {
                "range": {
                    "path": "datePublished",
                    "gte": __import__("datetime").datetime.min,
                    "score": {"boost": {"value": settings.SEARCH_BOOST_DATE_PUBLISHED}},
                }
            },
        ]

        self.assertEqual(stages[0]["$search"]["compound"]["filter"], expected_filter)
        self.assertEqual(stages[0]["$search"]["compound"]["must"], expected_must)
        self.assertEqual(stages[0]["$search"]["compound"]["should"], expected_should)
        self.assertEqual(stages[0]["$search"]["sort"], {"dateCreated": -1})
        self.assertEqual(stages[1]["$set"]["paginationToken"], {"$meta": "searchSequenceToken"})
        self.assertEqual(
            stages[2],
            {"$match": {"score": {"$gt": settings.SEARCH_RELEVANCE_SCORE_THRESHOLD}}},
        )

    def test_stages_multi_word_term_adds_phrase_boosts(self):
        term = "water velocity"

        search_query = SearchQuery(
            term=term,
            paginationToken=None,
        )

        stages = search_query.stages
        search_stage = stages[0]["$search"]

        self.assertEqual(search_stage["compound"]["should"], [
            {
                "phrase": {
                    "query": term,
                    "path": "name",
                    "score": {"boost": {"value": settings.SEARCH_BOOST_PHRASE_NAME}},
                }
            },
            {
                "phrase": {
                    "query": term,
                    "path": "description",
                    "score": {"boost": {"value": settings.SEARCH_BOOST_PHRASE_DESCRIPTION}},
                }
            },
            {
                "phrase": {
                    "query": term,
                    "path": "keywords",
                    "score": {"boost": {"value": settings.SEARCH_BOOST_PHRASE_KEYWORDS}},
                }
            },
            {
                "range": {
                    "path": "datePublished",
                    "gte": datetime.min,
                    "score": {"boost": {"value": settings.SEARCH_BOOST_DATE_PUBLISHED}},
                }
            },
        ])

    def test_stages_short_term_does_not_add_fuzzy_clause(self):
        term = "soil"

        search_query = SearchQuery(
            term=term,
            paginationToken=None,
        )

        stages = search_query.stages
        search_stage = stages[0]["$search"]

        should_clauses = search_stage["compound"]["must"][0]["compound"]["should"]

        self.assertFalse(any("fuzzy" in clause["autocomplete"] for clause in should_clauses))

    @parametrize(
        "sort_by,order,expected_sort",
        [
            param(None, None, {"dateModified": -1}, id="default_sort"),
            param("name", "asc", {"name": 1}, id="name_asc"),
            param("dateCreated", "asc", {"dateCreated": 1}, id="date_created_asc"),
            param("lastModified", "desc", {"dateModified": -1}, id="last_modified_desc"),
            param("creatorName", "asc", {"first_creator.name": 1}, id="creator_name_asc"),
            param("viewCount", "desc", {"viewCount": -1}, id="view_count_desc"),
        ],
    )
    def test_stages_respects_sort_(self, sort_by, order, expected_sort):
        search_query = SearchQuery(
            sortBy=sort_by,
            order=order,
            paginationToken=None,
        )

        stages = search_query.stages

        self.assertEqual(stages[0]["$search"]["sort"], expected_sort)

    def test_stages_multiple_content_types(self):
        content_types = ["CSVLogicalFile", "CollectionResource"]

        search_query = SearchQuery(
            contentType=content_types,
            paginationToken=None,
        )

        stages = search_query.stages

        self.assertEqual(len(stages), 2)

        self.assertEqual(stages[0]["$search"]["compound"]["must"], [
            {
                "compound": {
                    "should": [
                        {"term": {"path": "additionalType", "query": content_types[0]}},
                        {"term": {"path": "content_types", "query": content_types[0]}},
                        {"term": {"path": "additionalType", "query": content_types[1]}},
                        {"term": {"path": "content_types", "query": content_types[1]}},
                    ]
                }
            },
        ])

    def test_stages_multiple_creative_work_statuses(self):
        creative_work_statuses = ["Published", "Public"]

        search_query = SearchQuery(
            creativeWorkStatus=creative_work_statuses,
            paginationToken=None,
        )

        stages = search_query.stages

        self.assertEqual(stages[0]["$search"]["compound"]["must"], [
            {
                "compound": {
                    "should": [
                        {
                            "compound": {
                                "should": [
                                    {"term": {"path": "creativeWorkStatus", "query": creative_work_statuses[0]}},
                                    {"term": {"path": "creativeWorkStatus.name", "query": creative_work_statuses[0]}},
                                ]
                            }
                        },
                        {
                            "compound": {
                                "should": [
                                    {"term": {"path": "creativeWorkStatus", "query": creative_work_statuses[1]}},
                                    {"term": {"path": "creativeWorkStatus.name", "query": creative_work_statuses[1]}},
                                ]
                            }
                        },
                    ]
                }
            },
        ])


class TestSearchEndpointUnit(SimpleTestCase):

    @patch("hs_rest_api.discovery_atlas.MongoDBClient.get_discovery_collection")
    def test_search_endpoint(self, mock_get_discovery_collection):
        content_type = "CSVLogicalFile"
        pagination_token = "abc123"
        discovery_results = [{"resource_id": "res-1", "title": "Soil Resource"}]
        request_factory = APIRequestFactory()

        mock_collection = mock_get_discovery_collection.return_value
        mock_cursor = mock_collection.aggregate.return_value
        mock_cursor.to_list.return_value = discovery_results

        request = request_factory.get(
            f"/discovery-atlas/search?contentType={content_type}&paginationToken={pagination_token}"
        )
        response = discovery_atlas_search(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode()), discovery_results)

        aggregate_call_args = mock_collection.aggregate.call_args.args
        self.assertEqual(len(aggregate_call_args), 1)

        stages = aggregate_call_args[0]
        self.assertEqual(len(stages), 4)

        self.assertIn("$search", stages[0])
        self.assertEqual(stages[0]["$search"]["index"], "fuzzy_search")
        self.assertEqual(stages[0]["$search"]["searchAfter"], pagination_token)
        self.assertIn("compound", stages[0]["$search"])
        self.assertIn("$set", stages[1])
        self.assertEqual(
            stages[1]["$set"],
            {
                "score": {"$meta": "searchScore"},
                "highlights": {"$meta": "searchHighlights"},
                "paginationToken": {"$meta": "searchSequenceToken"},
            },
        )
        self.assertEqual(stages[2], {"$limit": 20})
        self.assertEqual(
            stages[3],
            {
                "$lookup": {
                    "from": "discovery",
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "document",
                }
            },
        )

        mock_collection.aggregate.assert_called_once()
        mock_cursor.to_list.assert_called_once_with(None)

    @patch("hs_rest_api.discovery_atlas.MongoDBClient.get_discovery_collection")
    def test_search_endpoint_validation_error_returns_400(self, mock_get_discovery_collection):
        request_factory = APIRequestFactory()
        request = request_factory.get("/discovery-atlas/search", {"dateCreatedStart": 10000}, format="json")

        response = discovery_atlas_search(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dateCreatedStart is not a valid year", json.loads(response.content.decode())["detail"])
        mock_get_discovery_collection.assert_not_called()
