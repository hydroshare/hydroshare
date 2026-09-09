import unittest
from unittest import mock
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_cloudnative_schemas.schema import base as schema
from hs_core.hydroshare_schemaorg_adapter import Contributor, Creator, HydroshareMetadataAdapter, Relation


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


class TestPersonIdentifierConversion(unittest.TestCase):
    """Creator/Contributor.identifier is now a list of PersonIdentifier objects
    (propertyID + value), built from the person's `identifiers` dict."""

    def test_creator_identifiers_convert_to_person_identifier_list(self):
        creator = Creator(
            name="Jane Smith",
            identifiers={
                "ORCID": "https://orcid.org/0000-0001-2345-6789",
                "ResearchGateID": "https://www.researchgate.net/profile/jane",
            },
        )
        result = creator.to_dataset_creator()

        self.assertIsInstance(result, schema.Creator)
        self.assertEqual(len(result.identifier), 2)
        by_property_id = {identifier.propertyID: str(identifier.value) for identifier in result.identifier}
        self.assertEqual(by_property_id["ORCID"], "https://orcid.org/0000-0001-2345-6789")
        self.assertEqual(by_property_id["ResearchGateID"], "https://www.researchgate.net/profile/jane")

    def test_contributor_with_no_identifiers_has_no_identifier_list(self):
        contributor = Contributor(name="John Doe", identifiers={})
        result = contributor.to_dataset_contributor()

        self.assertIsInstance(result, schema.Contributor)
        self.assertFalse(hasattr(result, "identifier") and result.identifier)

    def test_unsupported_identifier_key_is_skipped(self):
        creator = Creator(
            name="Jane Smith",
            identifiers={"HydroShareID": "https://www.hydroshare.org/user/123/", "Unknown": "https://example.com"},
        )
        result = creator.to_dataset_creator()

        # HydroShareID is a valid enum member (populated through a separate
        # mechanism, not from Party.identifiers) so it round-trips; "Unknown"
        # isn't a PersonIdentifierPropertyID member and is dropped.
        self.assertEqual(len(result.identifier), 1)
        self.assertEqual(result.identifier[0].propertyID, "HydroShareID")

    @mock.patch("hs_core.hydroshare.utils.current_site_url", return_value="https://www.hydroshare.org")
    def test_linked_hydroshare_user_gets_hydroshareid_identifier(self, _mock_site_url):
        creator = Creator(name="Jane Smith", identifiers={"ORCID": "https://orcid.org/0000-0001-2345-6789"},
                           hydroshare_user_id=123)
        result = creator.to_dataset_creator()

        by_property_id = {identifier.propertyID: str(identifier.value) for identifier in result.identifier}
        self.assertEqual(len(result.identifier), 2)
        self.assertEqual(by_property_id["HydroShareID"], "https://www.hydroshare.org/user/123/")
        self.assertEqual(by_property_id["ORCID"], "https://orcid.org/0000-0001-2345-6789")

    @mock.patch("hs_core.hydroshare.utils.current_site_url", return_value="https://www.hydroshare.org")
    def test_contributor_without_hydroshare_user_id_has_no_hydroshareid_identifier(self, _mock_site_url):
        contributor = Contributor(name="John Doe", identifiers={})
        result = contributor.to_dataset_contributor()

        self.assertFalse(hasattr(result, "identifier") and result.identifier)
        _mock_site_url.assert_not_called()


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
