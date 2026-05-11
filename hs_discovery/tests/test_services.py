from django.test import SimpleTestCase

from hs_discovery.services.atlas_search import AtlasSearchService, SearchQuery
from hs_discovery.services.query_mapper import build_search_query_from_form
from hs_discovery.services.result_mapper import map_atlas_result, map_atlas_results


class DiscoveryQueryMapperTests(SimpleTestCase):
    def test_build_search_query_from_form_maps_sort(self):
        query = build_search_query_from_form({
            "term": "water",
            "sort": "title",
            "enableContentType": True,
            "contentType": ["resource"],
            "enableAvailability": True,
            "creativeWorkStatus": ["Public"],
            "creatorName": "Jane Doe",
            "keyword": "streamflow",
            "enableDataCoverage": True,
            "dataCoverageStart": 2020,
            "dataCoverageEnd": 2021,
            "enableDateCreated": True,
            "dateCreatedStart": 2024,
            "dateCreatedEnd": 2025,
            "enablePublished": True,
            "publishedStart": 2023,
            "publishedEnd": 2024,
            "pageSize": 20,
            "paginationToken": None,
        })
        self.assertIsInstance(query, SearchQuery)
        self.assertEqual(query.sortBy, "name")
        self.assertEqual(query.order, "asc")
        self.assertEqual(query.contentType, ["CompositeResource"])
        self.assertEqual(query.creativeWorkStatus, ["Public"])
        self.assertEqual(query.dataCoverageStart, 2020)
        self.assertEqual(query.publishedEnd, 2024)


class DiscoverySearchQueryTests(SimpleTestCase):
    def test_explicit_sort_is_respected_without_term_or_filters(self):
        query = SearchQuery(sortBy="name", order="asc")
        self.assertEqual(query.stages[0]["$search"]["sort"], {"name": 1})

    def test_term_is_required_even_when_other_filters_are_present(self):
        query = SearchQuery(term="water", contentType=["CompositeResource"])
        must_clauses = query.stages[0]["$search"]["compound"]["must"]
        self.assertTrue(any(
            clause.get("compound", {}).get("minimumShouldMatch") == 1
            for clause in must_clauses
        ))

    def test_default_sort_is_last_modified_when_no_term_or_filters(self):
        query = SearchQuery()
        self.assertEqual(query.stages[0]["$search"]["sort"], {"dateModified": -1})

    def test_term_clauses_are_not_left_as_optional_should_when_term_present(self):
        query = SearchQuery(term="water", contentType=["CompositeResource"])
        should_clauses = query.stages[0]["$search"]["compound"]["should"]
        self.assertFalse(any(
            clause.get("autocomplete", {}).get("query") == "water"
            for clause in should_clauses
        ))

    def test_query_mapper_uses_requested_order(self):
        query = build_search_query_from_form({
            "term": "",
            "sort": "title",
            "order": "desc",
            "contentType": [],
            "creativeWorkStatus": [],
            "creatorName": "",
            "keyword": "",
            "fundingFunderName": "",
            "dataCoverageStart": None,
            "dataCoverageEnd": None,
            "dateCreatedStart": None,
            "dateCreatedEnd": None,
            "publishedStart": None,
            "publishedEnd": None,
            "pageSize": 20,
            "paginationToken": None,
        })
        self.assertEqual(query.sortBy, "name")
        self.assertEqual(query.order, "desc")

    def test_content_type_filter_expands_grouped_values(self):
        query = build_search_query_from_form({
            "sort": "relevance",
            "enableContentType": True,
            "contentType": ["geographic-feature", "time-series"],
            "creativeWorkStatus": [],
            "creatorName": "",
            "keyword": "",
            "fundingFunderName": "",
            "dataCoverageStart": None,
            "dataCoverageEnd": None,
            "dateCreatedStart": None,
            "dateCreatedEnd": None,
            "publishedStart": None,
            "publishedEnd": None,
            "pageSize": 20,
            "paginationToken": None,
        })
        self.assertEqual(
            query.contentType,
            [
                "GeoFeatureLogicalFile",
                "GeographicFeatureAggregation",
                "TimeSeriesLogicalFile",
                "TimeSeriesAggregation",
            ],
        )


class FakeAggregateResult:
    def __init__(self, data):
        self.data = data

    def to_list(self, _length):
        return self.data


class RecordingCollection:
    def __init__(self, *, count_result=None, search_result=None, typeahead_result=None):
        self.count_result = count_result if count_result is not None else [{'total': 42}]
        self.search_result = search_result if search_result is not None else [
            {
                '_id': 'abc123',
                'paginationToken': 'tok-1',
                'highlights': [],
                'document': [{
                    'name': 'Water Resource',
                    'identifier': ['/resource/abc123/'],
                    'creator': [{'name': 'Jane Doe'}],
                    'description': 'A useful record',
                    'additionalType': 'CompositeResource',
                    'creativeWorkStatus': {'name': 'Public'},
                }],
            }
        ]
        self.typeahead_result = typeahead_result if typeahead_result is not None else []
        self.calls = []

    def aggregate(self, stages):
        self.calls.append(stages)
        if stages and stages[-1] == {'$count': 'total'}:
            return FakeAggregateResult(self.count_result)
        if any('$project' in stage for stage in stages):
            return FakeAggregateResult(self.typeahead_result)
        return FakeAggregateResult(self.search_result)


class AtlasSearchServiceTests(SimpleTestCase):
    def test_search_includes_total_count(self):
        service = AtlasSearchService(collection=RecordingCollection())
        results = service.search(SearchQuery(pageSize=5))
        self.assertEqual(results.total_count, 42)
        self.assertEqual(len(results.items), 1)

    def test_search_raw_applies_skip_and_limit_on_first_page(self):
        collection = RecordingCollection(search_result=[
            {'_id': '1', 'paginationToken': 'a', 'highlights': [], 'document': [{'name': 'One'}]},
            {'_id': '2', 'paginationToken': 'b', 'highlights': [], 'document': [{'name': 'Two'}]},
            {'_id': '3', 'paginationToken': 'c', 'highlights': [], 'document': [{'name': 'Three'}]},
        ])
        service = AtlasSearchService(collection=collection)
        raw_results, has_more, total_count = service.search_raw(SearchQuery(pageNumber=2, pageSize=2))
        self.assertEqual(total_count, 42)
        self.assertTrue(has_more)
        self.assertEqual(len(raw_results), 2)
        search_call = collection.calls[1]
        self.assertIn({'$skip': 2}, search_call)
        self.assertIn({'$limit': 3}, search_call)

    def test_search_raw_uses_search_after_without_skip_when_pagination_token_present(self):
        collection = RecordingCollection()
        service = AtlasSearchService(collection=collection)
        service.search_raw(SearchQuery(pageSize=5, paginationToken='tok-123'))
        count_call = collection.calls[0]
        search_call = collection.calls[1]
        self.assertEqual(count_call[-1], {'$count': 'total'})
        self.assertNotIn({'$skip': 0}, search_call)
        self.assertIn({'$limit': 6}, search_call)
        self.assertEqual(search_call[0]['$search']['searchAfter'], 'tok-123')

    def test_search_returns_zero_total_count_when_count_pipeline_is_empty(self):
        service = AtlasSearchService(collection=RecordingCollection(count_result=[]))
        results = service.search(SearchQuery(pageSize=5))
        self.assertEqual(results.total_count, 0)

    def test_typeahead_uses_term_paths_by_default(self):
        collection = RecordingCollection(typeahead_result=[{'name': 'Water'}])
        service = AtlasSearchService(collection=collection)
        payload = service.typeahead('wat', 'term')
        self.assertEqual(payload, [{'name': 'Water'}])
        search_call = collection.calls[0]
        should = search_call[0]['$search']['compound']['should']
        paths = [clause['autocomplete']['path'] for clause in should]
        self.assertEqual(paths, ['name', 'description', 'keywords', 'creator.name'])

    def test_typeahead_uses_creator_paths_for_creator_field(self):
        collection = RecordingCollection()
        service = AtlasSearchService(collection=collection)
        service.typeahead('jane', 'creator')
        should = collection.calls[0][0]['$search']['compound']['should']
        paths = [clause['autocomplete']['path'] for clause in should]
        self.assertEqual(paths, ['creator.name', 'contributor.name'])

    def test_typeahead_uses_subject_paths_for_subject_field(self):
        collection = RecordingCollection()
        service = AtlasSearchService(collection=collection)
        service.typeahead('snow', 'subject')
        should = collection.calls[0][0]['$search']['compound']['should']
        paths = [clause['autocomplete']['path'] for clause in should]
        self.assertEqual(paths, ['keywords'])

    def test_typeahead_uses_funder_paths_for_funder_field(self):
        collection = RecordingCollection()
        service = AtlasSearchService(collection=collection)
        service.typeahead('nsf', 'funder')
        should = collection.calls[0][0]['$search']['compound']['should']
        paths = [clause['autocomplete']['path'] for clause in should]
        self.assertEqual(paths, ['funding.funder.name'])


class DiscoveryResultMapperTests(SimpleTestCase):
    def test_map_atlas_results_uses_last_item_token_when_has_more(self):
        results = map_atlas_results(
            [
                {
                    "_id": "abc123",
                    "paginationToken": "tok-1",
                    "highlights": [],
                    "document": [{"name": "One", "identifier": ["/resource/one/"]}],
                },
                {
                    "_id": "def456",
                    "paginationToken": "tok-2",
                    "highlights": [],
                    "document": [{"name": "Two", "identifier": ["/resource/two/"]}],
                },
            ],
            has_more=True,
            total_count=8,
        )
        self.assertEqual(results.next_pagination_token, "tok-2")
        self.assertEqual(results.total_count, 8)

    def test_map_atlas_results_omits_next_token_when_has_more_is_false(self):
        results = map_atlas_results(
            [
                {
                    "_id": "abc123",
                    "paginationToken": "tok-1",
                    "highlights": [],
                    "document": [{"name": "One", "identifier": ["/resource/one/"]}],
                }
            ],
            has_more=False,
        )
        self.assertIsNone(results.next_pagination_token)

    def test_map_atlas_result(self):
        result = map_atlas_result({
            "_id": "abc123",
            "paginationToken": "tok-1",
            "highlights": [{"path": "name", "texts": [{"type": "hit", "value": "Water"}]}],
            "document": [{
                "name": "Water Resource",
                "identifier": ["/resource/abc123/"],
                "creator": [{"name": "Jane Doe"}],
                "contributor": [{"name": "John Smith"}],
                "description": "A useful record",
                "keywords": ["water", {"name": "hydrology"}],
                "additionalType": "CompositeResource",
                "creativeWorkStatus": {"name": "Public"},
                "dateCreated": "2024-01-01T00:00:00",
                "dateModified": "2024-02-01T00:00:00",
            }],
        })
        self.assertEqual(result.id, "abc123")
        self.assertEqual(result.identifier, "/resource/abc123/")
        self.assertEqual(result.authors, ["Jane Doe"])
        self.assertEqual(result.contributors, ["John Smith"])
        self.assertEqual(result.resource_type, "CompositeResource")
        self.assertEqual(result.sharing_status, "Public")
        self.assertIn("<mark>Water</mark>", result.title_html)
