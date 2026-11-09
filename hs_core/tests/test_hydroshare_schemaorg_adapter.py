import json
import unittest
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_cloudnative_schemas.schema import base as schema
from hs_core.hydroshare_schemaorg_adapter import HydroshareMetadataAdapter, Relation


IS_PART_OF_VALUE = "The content of this resource is part of"
HAS_PART_VALUE = "This resource includes"
REFERENCES_VALUE = "The content of this resource references"

MINIMAL_METADATA = {
    "type": "CompositeResource",
    "title": "Test Resource",
}


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


class TestToCatalogRecordRelationPartitioning(unittest.TestCase):
    """Tests that relations are routed to the correct fields and are not duplicated."""

    def test_is_part_of_only_appears_in_is_part_of(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [{"type": IS_PART_OF_VALUE, "value": "A collection, https://www.hydroshare.org/resource/abc"}],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
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
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
        self.assertEqual(len(dataset.hasPart), 1)
        self.assertEqual(len(dataset.isPartOf), 0)
        self.assertEqual(len(dataset.relation), 0)

    def test_other_relation_only_appears_in_relations(self):
        metadata = {
            **MINIMAL_METADATA,
            "relations": [{"type": REFERENCES_VALUE, "value": "A paper, https://doi.org/10.1234/abc"}],
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
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
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
        self.assertEqual(len(dataset.isPartOf), 1)
        self.assertEqual(len(dataset.hasPart), 1)
        self.assertEqual(len(dataset.relation), 1)


class TestToCatalogRecordAdditionalMetadata(unittest.TestCase):
    """Tests that hsmodels additional_metadata maps to schema.org additionalProperty."""

    def test_additional_metadata_maps_to_additional_property(self):
        metadata = {
            **MINIMAL_METADATA,
            "additional_metadata": {"site": "Logan River", "depth": "2 m"},
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
        self.assertEqual(len(dataset.additionalProperty), 2)
        for prop in dataset.additionalProperty:
            self.assertIsInstance(prop, schema.PropertyValue)
        self.assertEqual(
            {p.name: p.value for p in dataset.additionalProperty},
            {"site": "Logan River", "depth": "2 m"},
        )

    def test_empty_additional_metadata_yields_no_additional_property(self):
        metadata = {**MINIMAL_METADATA, "additional_metadata": {}}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata)
        self.assertIsNone(dataset.additionalProperty)

    def test_missing_additional_metadata_yields_no_additional_property(self):
        dataset = HydroshareMetadataAdapter.to_catalog_record(MINIMAL_METADATA)
        self.assertIsNone(dataset.additionalProperty)

    def test_additional_metadata_key_not_in_dumped_record(self):
        metadata = {**MINIMAL_METADATA, "additional_metadata": {"site": "Logan River"}}
        dumped = HydroshareMetadataAdapter.to_catalog_record(metadata).model_dump(by_alias=True)
        self.assertNotIn("additional_metadata", dumped)
        self.assertEqual(dumped["additionalProperty"][0]["@type"], "PropertyValue")
        self.assertEqual(dumped["additionalProperty"][0]["name"], "site")
        self.assertEqual(dumped["additionalProperty"][0]["value"], "Logan River")


# Input shaped like what write_user_metadata_json_file() passes to the adapter: the hsmodels
# ResourceMetadata keys plus the extra keys injected in hs_core/models.py.
REALISTIC_METADATA = {
    "type": "CompositeResource",
    "title": "Test Resource",
    "abstract": "An abstract",
    "url": "https://www.hydroshare.org/resource/abc123/",
    "identifier": "https://www.hydroshare.org/resource/abc123/",
    "creators": [{"name": "Doe, Jane"}],
    "contributors": [],
    "created": "2026-01-01T00:00:00+00:00",
    "modified": "2026-01-02T00:00:00+00:00",
    "subjects": ["water"],
    "language": "eng",
    "rights": {
        "statement": "CC BY",
        "url": "http://creativecommons.org/licenses/by/4.0/",
    },
    "awards": [],
    "relations": [{"type": REFERENCES_VALUE, "value": "A paper, https://doi.org/10.1234/abc"}],
    "citation": "Doe, J. (2026). Test Resource, HydroShare",
    "additional_metadata": {"key": "value"},
    "publisher": None,
    "review_started": "2026-01-03T00:00:00+00:00",
    "sharing_status": "public",
    "viewCount": 42,
    "content_types": ["CompositeResource"],
}

# Keys that must never appear in the generated schema.org metadata
NON_COMPLIANT_KEYS = {"sharing_status", "viewCount", "review_started"}


def _generate_user_metadata(metadata):
    """Serialize the adapter output the same way hs_core.models.write_user_metadata_json_file does."""
    dataset = HydroshareMetadataAdapter.to_catalog_record(dict(metadata))
    dumped = dataset.model_dump(exclude={'dateCreated', 'dateModified', 'datePublished'}, by_alias=True)
    return json.loads(json.dumps(dumped, default=str))


class TestToCatalogRecordSchemaOrgCompliance(ParametrizedTestCase):
    """Tests that non schema.org compliant fields are not included in the generated metadata."""

    def test_non_compliant_keys_are_not_emitted(self):
        for metadata in (REALISTIC_METADATA, MINIMAL_METADATA):
            output = _generate_user_metadata(metadata)
            self.assertEqual(NON_COMPLIANT_KEYS & output.keys(), set())

    def test_creative_work_status_is_none_without_sharing_status(self):
        """No default status is invented when the input has no sharing_status."""
        output = _generate_user_metadata(MINIMAL_METADATA)
        self.assertIsNone(output["creativeWorkStatus"])

    @parametrize(
        "sharing_status,expected_name",
        [
            param("public", "Public", id="public"),
            param("private", "Private", id="private"),
            param("published", "Published", id="published"),
            param("discoverable", "Discoverable", id="discoverable"),
        ],
    )
    def test_sharing_status_maps_to_creative_work_status(self, sharing_status, expected_name):
        output = _generate_user_metadata({**REALISTIC_METADATA, "sharing_status": sharing_status})
        self.assertNotIn("sharing_status", output)
        self.assertEqual(output["creativeWorkStatus"]["name"], expected_name)
