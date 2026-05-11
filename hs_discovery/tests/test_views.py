from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from pymongo.errors import PyMongoError

from hs_discovery.services.result_mapper import DiscoveryResult, DiscoverySearchResults


class DiscoveryViewsTests(TestCase):
    def _mock_results(self):
        return DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="abc123",
                    title="Water Resource",
                    title_html="Water Resource",
                    identifier="/resource/abc123/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="A useful resource",
                    abstract_html="A useful resource",
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    created="2026-05-08T14:30:00Z",
                    modified="2026-11-03",
                    pagination_token="tok-1",
                )
            ],
            next_pagination_token="tok-1",
            has_more=True,
            total_count=12,
        )

    def _mock_results_with_long_abstract(self):
        return DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="abc123",
                    title="Water Resource",
                    title_html="Water Resource",
                    identifier="/resource/abc123/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="A" * 500,
                    abstract_html="A" * 500,
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    pagination_token="tok-1",
                )
            ],
            next_pagination_token="tok-1",
            has_more=True,
        )

    def _mock_results_with_spatial_coverage(self):
        return DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="abc123",
                    title="Water Resource",
                    title_html="Water Resource",
                    identifier="/resource/abc123/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="A useful resource",
                    abstract_html="A useful resource",
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    spatial_coverage={
                        "type": "GeoCoordinates",
                        "latitude": 38.5,
                        "longitude": -100.2,
                    },
                    pagination_token="tok-1",
                )
            ],
            next_pagination_token="tok-1",
            has_more=True,
        )

    def _mock_empty_results(self):
        return DiscoverySearchResults(
            items=[],
            next_pagination_token=None,
            has_more=False,
            total_count=0,
        )

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_page_view_renders(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Discover")
        self.assertContains(response, "Water Resource")
        self.assertContains(response, "5/08/2026")
        self.assertContains(response, "11/03/2026")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_page_view_renders_with_empty_querydict(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:page"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Water Resource")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_results_partial_renders(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:results"), {"term": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Water Resource")
        self.assertContains(response, "Load more")
        self.assertContains(response, "<strong>12</strong> results", html=True)

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_more_partial_renders(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:more"), {"paginationToken": "tok-1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "hx-swap-oob")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_load_more_button_includes_next_pagination_token_and_existing_filters(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {"keyword": "streamflow", "pageSize": 5},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'hx-get="/search-v2/more/?keyword=streamflow&amp;pageSize=5&amp;paginationToken=tok-1"',
        )

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_load_more_button_omits_stale_pagination_token_from_request(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {"keyword": "streamflow", "pageSize": 5, "paginationToken": "old-token"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'hx-get="/search-v2/more/?keyword=streamflow&amp;pageSize=5&amp;paginationToken=tok-1"',
        )
        self.assertNotContains(response, "old-token")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_more_partial_updates_load_more_button_to_next_token(self, mock_search):
        mock_search.return_value = DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="def456",
                    title="Second Resource",
                    title_html="Second Resource",
                    identifier="/resource/def456/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="Another useful resource",
                    abstract_html="Another useful resource",
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    pagination_token="tok-2",
                )
            ],
            next_pagination_token="tok-2",
            has_more=True,
            total_count=12,
        )
        response = self.client.get(
            reverse("discovery:more"),
            {"keyword": "streamflow", "pageSize": 5, "paginationToken": "tok-1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Second Resource")
        self.assertContains(
            response,
            'hx-get="/search-v2/more/?keyword=streamflow&amp;pageSize=5&amp;paginationToken=tok-2"',
        )
        self.assertNotContains(response, "paginationToken=tok-1")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_more_partial_does_not_replace_total_count_header(self, mock_search):
        mock_search.return_value = DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="def456",
                    title="Second Resource",
                    title_html="Second Resource",
                    identifier="/resource/def456/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="Another useful resource",
                    abstract_html="Another useful resource",
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    pagination_token="tok-2",
                )
            ],
            next_pagination_token="tok-2",
            has_more=True,
            total_count=12,
        )
        response = self.client.get(
            reverse("discovery:more"),
            {"keyword": "streamflow", "pageSize": 5, "paginationToken": "tok-1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Second Resource")
        self.assertNotContains(response, "discovery-results-count")
        self.assertNotContains(response, "<strong>12</strong> results", html=True)

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_more_partial_shows_end_of_results_when_no_next_token(self, mock_search):
        mock_search.return_value = DiscoverySearchResults(
            items=[
                DiscoveryResult(
                    id="ghi789",
                    title="Last Resource",
                    title_html="Last Resource",
                    identifier="/resource/ghi789/",
                    authors=["Jane Doe"],
                    authors_html="Jane Doe",
                    abstract="Final useful resource",
                    abstract_html="Final useful resource",
                    resource_type="CompositeResource",
                    sharing_status="Public",
                    pagination_token="tok-final",
                )
            ],
            next_pagination_token=None,
            has_more=False,
            total_count=12,
        )
        response = self.client.get(
            reverse("discovery:more"),
            {"keyword": "streamflow", "pageSize": 5, "paginationToken": "tok-2"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Last Resource")
        self.assertContains(response, "End of results.")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_page_view_handles_pymongo_error(self, mock_search):
        mock_search.side_effect = PyMongoError("mongo down")
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Discovery search is temporarily unavailable")
        self.assertContains(response, "No results found for the current search and filters.")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_results_partial_handles_pymongo_error(self, mock_search):
        mock_search.side_effect = PyMongoError("mongo down")
        response = self.client.get(reverse("discovery:results"), {"term": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Discovery search is temporarily unavailable")
        self.assertContains(response, "No results found for the current search and filters.")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_more_partial_handles_pymongo_error(self, mock_search):
        mock_search.side_effect = PyMongoError("mongo down")
        response = self.client.get(reverse("discovery:more"), {"paginationToken": "tok-1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No results found for the current search and filters.")
        self.assertContains(response, "End of results.")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_results_partial_renders_zero_total_count(self, mock_search):
        mock_search.return_value = self._mock_empty_results()
        response = self.client.get(reverse("discovery:results"), {"term": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>0</strong> results", html=True)
        self.assertContains(response, "End of results.")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_active_filter_chips_render_with_htmx_remove_links(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {
                "keyword": "streamflow",
                "enableContentType": "1",
                "contentType": ["resource", "collection-resource"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Active filters:")
        self.assertContains(response, "Keyword: streamflow")
        self.assertContains(response, "Content type: Resource")
        self.assertContains(response, "Content type: Collection")
        self.assertContains(response, 'data-filter-key="keyword"')
        self.assertContains(response, 'data-filter-key="contentType"')
        self.assertContains(response, 'hx-get="/search-v2/results/?')

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_search_term_is_not_rendered_as_active_filter_chip(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {
                "term": "water",
                "keyword": "streamflow",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Keyword: streamflow")
        self.assertNotContains(response, "Search: water")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_search_toolbar_renders_clear_term_control(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:page"), {"term": "water"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "discovery-main-search-clear")
        self.assertContains(response, "term-cleared")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_active_filter_chip_remove_link_excludes_removed_value(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {
                "enableContentType": "1",
                "contentType": ["resource", "collection-resource"],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "contentType=collection-resource")
        self.assertContains(response, "enableContentType=1")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_expanded_details_show_more_for_long_abstract(self, mock_search):
        mock_search.return_value = self._mock_results_with_long_abstract()
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SHOW MORE")
        self.assertContains(response, "SHOW LESS")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_spatial_coverage_renders_map_container(self, mock_search):
        mock_search.return_value = self._mock_results_with_spatial_coverage()
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "discovery-spatial-map")
        self.assertContains(response, 'data-spatial-type="GeoCoordinates"')
        self.assertContains(response, 'data-latitude="38.5"')
        self.assertContains(response, 'data-longitude="-100.2"')

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_sort_dropdown_links_include_expected_sort_query(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'hx-get="/search-v2/results/?sort=title&amp;order=asc"')

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_range_filter_chip_remove_link_clears_range_keys(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(
            reverse("discovery:page"),
            {
                "enableDataCoverage": "1",
                "dataCoverageStart": 2011,
                "dataCoverageEnd": 2015,
                "keyword": "streamflow",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Temporal coverage: 2011 to 2015")
        self.assertContains(response, "Keyword: streamflow")
        self.assertContains(response, "hx-get=\"/search-v2/results/?keyword=streamflow\"")

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_content_type_filter_not_applied_when_toggle_disabled(self, mock_search):
        mock_search.return_value = self._mock_results()
        self.client.get(
            reverse("discovery:page"),
            {
                "contentType": ["CompositeResource", "CollectionResource"],
            },
        )
        search_query = mock_search.call_args.args[0]
        self.assertEqual(search_query.contentType, [])

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_content_type_filter_applied_when_toggle_enabled(self, mock_search):
        mock_search.return_value = self._mock_results()
        self.client.get(
            reverse("discovery:page"),
            {
                "enableContentType": "1",
                "contentType": ["resource", "collection-resource"],
            },
        )
        search_query = mock_search.call_args.args[0]
        self.assertEqual(search_query.contentType, ["CompositeResource", "CollectionResource"])

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_temporal_range_not_applied_when_toggle_disabled(self, mock_search):
        mock_search.return_value = self._mock_results()
        self.client.get(
            reverse("discovery:page"),
            {
                "dataCoverageStart": 2001,
                "dataCoverageEnd": 2005,
            },
        )
        search_query = mock_search.call_args.args[0]
        self.assertIsNone(search_query.dataCoverageStart)
        self.assertIsNone(search_query.dataCoverageEnd)

    @patch("hs_discovery.views.AtlasSearchService.search")
    def test_discovery_templates_do_not_use_bootstrap_collapse_hooks(self, mock_search):
        mock_search.return_value = self._mock_results()
        response = self.client.get(reverse("discovery:page"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "data-parent=\"#discovery-filter-accordion\"")
        self.assertNotContains(response, "href=\"#temporal-coverage-panel\"")
        self.assertNotContains(response, "href=\"#content-type-panel\"")
        self.assertNotContains(response, "<details class=\"panel panel-default discovery-filter-section\" open>")
        self.assertContains(response, "name=\"enableDataCoverage\"")
        self.assertContains(response, "name=\"enableContentType\"")
