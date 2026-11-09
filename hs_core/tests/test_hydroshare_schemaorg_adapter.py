import unittest
from unittest_parametrize import ParametrizedTestCase, parametrize, param
from pydantic import ValidationError

from hs_cloudnative_schemas.schema import base as schema
from hs_core.hydroshare.utils import current_site_url
from hs_core.hydroshare_schemaorg_adapter import HydroshareMetadataAdapter, Relation


IS_PART_OF_VALUE = "The content of this resource is part of"
HAS_PART_VALUE = "This resource includes"
REFERENCES_VALUE = "The content of this resource references"

MINIMAL_METADATA = {
    "type": "CompositeResource",
    "title": "Test Resource",
}

RESOURCE_ID = "bbbb0000000000000000000000000003"


class TestRelationToDatasetRelation(ParametrizedTestCase):
    """Tests for Relation.to_dataset_relation() — URL/description parsing and schema object type."""

    @parametrize(
        "value,expected_description,expected_url",
        [
            param(
                "Smith, J. (2020). A paper, https://doi.org/10.1234/abc",
                "Smith, J. (2020). A paper",
                "https://doi.org/10.1234/abc",
                id="valid_url_after_last_comma",
            ),
            param(
                "Smith, J. (2020). A paper ending with nationalmap.gov/viewer/).",
                "Smith, J. (2020). A paper ending with nationalmap.gov/viewer/).",
                None,
                id="no_comma_no_url",
            ),
            param(
                "Smith, J. (2020). A paper, nationalmap.gov/viewer/).",
                "Smith, J. (2020). A paper, nationalmap.gov/viewer/).",
                None,
                id="non_url_after_last_comma",
            ),
            param(
                "Smith, J. (2020). A paper, available at https://nationalmap.gov/viewer/",
                "Smith, J. (2020). A paper, available at https://nationalmap.gov/viewer/",
                None,
                id="url_with_text_in_front",
            ),
        ],
    )
    def test_description_and_url_parsing(self, value, expected_description, expected_url):
        """URL is only set when the text after the last comma is a valid URL; otherwise
        it is folded back into the description."""
        relation = Relation(type=REFERENCES_VALUE, value=value)
        result = relation.to_dataset_relation()

        self.assertEqual(result.description, expected_description)
        if expected_url is None:
            self.assertIsNone(result.url)
        else:
            self.assertIsNotNone(result.url)
            self.assertEqual(str(result.url), expected_url)

    def test_is_part_of_relation_type(self):
        """An isPartOf relation yields an IsPartOf schema object with description set."""
        relation = Relation(
            type=IS_PART_OF_VALUE,
            value="Some collection, https://www.hydroshare.org/resource/abc123",
        )
        result = relation.to_dataset_relation()
        self.assertEqual(str(result.url), "https://www.hydroshare.org/resource/abc123")
        self.assertIsInstance(result, schema.IsPartOf)
        self.assertEqual(result.description, "Some collection")

    def test_has_part_relation_type(self):
        """A hasPart relation yields a HasPart schema object with description set."""
        relation = Relation(
            type=HAS_PART_VALUE,
            value="A contained resource, https://www.hydroshare.org/resource/def456",
        )
        result = relation.to_dataset_relation()
        self.assertEqual(str(result.url), "https://www.hydroshare.org/resource/def456")
        self.assertIsInstance(result, schema.HasPart)
        self.assertEqual(result.description, "A contained resource")

    def test_other_relation_type_sets_name(self):
        """Any relation_type other than HasPart or IsPartOf yields a Relation schema object with name set."""
        relation = Relation(type=REFERENCES_VALUE, value="Some value")
        result = relation.to_dataset_relation()
        self.assertIsInstance(result, schema.Relation)
        self.assertEqual(result.name, REFERENCES_VALUE)


class TestToCatalogRecordUrl(ParametrizedTestCase):
    """Tests that dataset.url is the DOI for published resources and the HydroShare resource URL otherwise."""

    SHORT_ID = "bbbb0000000000000000000000000003"
    LOCAL_URL = f"http://localhost:8000/resource/{SHORT_ID}"

    @parametrize(
        "sharing_status,is_doi",
        [
            param("published", True, id="published_uses_doi"),
            param("public", False, id="public_uses_site_url"),
            param("private", False, id="private_uses_site_url"),
            param("discoverable", False, id="discoverable_uses_site_url"),
            param(None, False, id="no_sharing_status_uses_site_url"),
        ],
    )
    def test_url_by_sharing_status(self, sharing_status, is_doi):
        expected_url = (
            f"https://doi.org/10.4211/hs.{self.SHORT_ID}" if is_doi
            else f"{current_site_url()}/resource/{self.SHORT_ID}"
        )
        metadata = {
            **MINIMAL_METADATA,
            "url": self.LOCAL_URL,
            "identifier": self.LOCAL_URL,
            "sharing_status": sharing_status,
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=self.SHORT_ID)
        self.assertEqual(str(dataset.url), expected_url)

    def test_url_uses_resource_id_not_metadata_url(self):
        metadata = {
            **MINIMAL_METADATA,
            "url": "http://localhost:8000/resource/someotherid",
            "sharing_status": "published",
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=self.SHORT_ID)
        self.assertEqual(str(dataset.url), f"https://doi.org/10.4211/hs.{self.SHORT_ID}")


class TestToCatalogRecordRelationPartitioning(unittest.TestCase):
    """Tests that relations are routed to the correct fields and are not duplicated."""

    def test_is_part_of_only_appears_in_is_part_of(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [{"type": IS_PART_OF_VALUE, "value": "A collection, https://www.hydroshare.org/resource/abc"}],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.isPartOf), 1)
        self.assertEqual(len(dataset.hasPart), 0)
        self.assertEqual(len(dataset.relation), 0)

    def test_has_part_only_appears_in_has_part(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [{
                "type": HAS_PART_VALUE,
                "value": "A child resource, https://www.hydroshare.org/resource/def"
            }],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.hasPart), 1)
        self.assertEqual(len(dataset.isPartOf), 0)
        self.assertEqual(len(dataset.relation), 0)

    def test_other_relation_only_appears_in_relations(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [{"type": REFERENCES_VALUE, "value": "A paper, https://doi.org/10.1234/abc"}],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.relation), 1)
        self.assertEqual(len(dataset.isPartOf), 0)
        self.assertEqual(len(dataset.hasPart), 0)

    def test_mixed_relations_assigned_correctly(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [
                {"type": IS_PART_OF_VALUE, "value": "A collection, https://www.hydroshare.org/resource/abc"},
                {"type": HAS_PART_VALUE, "value": "A child, https://www.hydroshare.org/resource/def"},
                {"type": REFERENCES_VALUE, "value": "A paper, https://doi.org/10.1234/abc"},
            ],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.isPartOf), 1)
        self.assertEqual(len(dataset.hasPart), 1)
        self.assertEqual(len(dataset.relation), 1)

class TestToCatalogRecordLanguage(unittest.TestCase):
    """Tests that HydroShare language codes map to schema.org inLanguage values."""

    def test_english_maps_to_en(self):
        metadata = {**MINIMAL_METADATA, "language": "eng"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.inLanguage, "en")

    def test_spanish_maps_to_es(self):
        metadata = {**MINIMAL_METADATA, "language": "spa"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.inLanguage, "es")

    def test_unknown_language_kept_as_other(self):
        metadata = {**MINIMAL_METADATA, "language": "fra"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsInstance(dataset.inLanguage, schema.InLanguageStr)
        self.assertEqual(dataset.inLanguage, "fra")

    def test_no_language_results_in_none(self):
        metadata = {**MINIMAL_METADATA, "language": None}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.inLanguage)


class TestToCatalogRecordTemporalCoverage(unittest.TestCase):
    """Tests that period coverage maps to a schema.org text interval of dates."""

    def test_timestamps_map_to_date_interval(self):
        metadata = {
            **MINIMAL_METADATA,
            "period_coverage": {"start": "2018-10-01T00:00:00", "end": "2022-09-30T00:00:00"},
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.temporalCoverage, "2018-10-01/2022-09-30")

    def test_date_only_input_maps_to_date_interval(self):
        metadata = {
            **MINIMAL_METADATA,
            "period_coverage": {"start": "2018-10-01", "end": "2022-09-30"},
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.temporalCoverage, "2018-10-01/2022-09-30")

    def test_no_period_coverage_results_in_none(self):
        metadata = {**MINIMAL_METADATA, "period_coverage": None}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.temporalCoverage)

    def test_missing_end_is_rejected(self):
        metadata = {**MINIMAL_METADATA, "period_coverage": {"start": "2018-10-01"}}
        with self.assertRaises(ValidationError):
            HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)


class TestToCatalogRecordProvider(unittest.TestCase):
    """Tests that the HydroShare provider carries a schema.org @id and homepage url."""

    def test_provider_has_id_and_url(self):
        dataset = HydroshareMetadataAdapter.to_catalog_record(MINIMAL_METADATA, resource_id=RESOURCE_ID)
        provider = dataset.model_dump(mode="json", by_alias=True, exclude_none=True)["provider"]
        self.assertEqual(provider["@id"], "https://hydroshare.org/")
        self.assertEqual(provider["url"], "https://hydroshare.org/")
        self.assertEqual(provider["name"], "HydroShare")


class TestToCatalogRecordKeywords(unittest.TestCase):
    """Tests that keywords are correctly extracted from subjects."""

    def test_keywords_from_subjects(self):
        metadata = {
            **MINIMAL_METADATA,
            "subjects": ["subject1", "subject2"]
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.keywords, ["subject1", "subject2"])

    def test_no_subjects_results_in_no_keywords(self):
        metadata = {
            **MINIMAL_METADATA,
            "subjects": None
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.keywords)


class TestToCatalogSpatialCoverage(unittest.TestCase):
    """Tests that spatial coverage is correctly extracted from metadata."""

    def test_spatial_coverage_box(self):
        metadata = {
            **MINIMAL_METADATA,
            "spatial_coverage": {
                "name": "Test Box",
                "northlimit": 10.0,
                "eastlimit": 20.0,
                "southlimit": 5.0,
                "westlimit": 15.0
            }
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.spatialCoverage.geo.box, "5.0 15.0 10.0 20.0")
        self.assertEqual(dataset.spatialCoverage.name, "Test Box")

    def test_spatial_coverage_point(self):
        metadata = {
            **MINIMAL_METADATA,
            "spatial_coverage": {
                "name": "Test Point",
                "north": 10.0,
                "east": 20.0
            }
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.spatialCoverage.geo.latitude, 10.0)
        self.assertEqual(dataset.spatialCoverage.geo.longitude, 20.0)
        self.assertEqual(dataset.spatialCoverage.name, "Test Point")
