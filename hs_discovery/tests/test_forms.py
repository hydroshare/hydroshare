from django.test import SimpleTestCase

from hs_discovery.forms import CURRENT_YEAR, DISCOVERY_MIN_YEAR, TEMPORAL_MIN_YEAR, DiscoverySearchForm


class DiscoverySearchFormTests(SimpleTestCase):
    def test_form_defaults(self):
        form = DiscoverySearchForm({})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["sort"], "relevance")
        self.assertIsNone(form.cleaned_data["order"])
        self.assertEqual(form.cleaned_data["pageSize"], 20)

    def test_form_trims_text_fields(self):
        form = DiscoverySearchForm({"term": "  water  ", "creatorName": "  Jane Doe  ", "keyword": "  snow  "})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["term"], "water")
        self.assertEqual(form.cleaned_data["creatorName"], "Jane Doe")
        self.assertEqual(form.cleaned_data["keyword"], "snow")

    def test_form_accepts_year_filters(self):
        form = DiscoverySearchForm({
            "dataCoverageStart": 2020,
            "dataCoverageEnd": 2021,
            "dateCreatedStart": 2024,
            "dateCreatedEnd": 2025,
            "publishedStart": 2023,
            "publishedEnd": 2024,
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["dataCoverageStart"], 2020)
        self.assertEqual(form.cleaned_data["publishedEnd"], 2024)

    def test_form_uses_discovery_year_bounds(self):
        self.assertEqual(TEMPORAL_MIN_YEAR, 2010)
        self.assertEqual(DISCOVERY_MIN_YEAR, 2010)
        self.assertGreaterEqual(CURRENT_YEAR, DISCOVERY_MIN_YEAR)
