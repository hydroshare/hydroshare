from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_cloudnative_schemas.schema import base as schema
from hs_core.hydroshare_schemaorg_adapter import Relation


class TestRelationToDatasetPartRelation(ParametrizedTestCase):
    """Tests for Relation.to_dataset_part_relation() — specifically the URL/description
    parsing logic that splits on the last comma of the relation value."""

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
        relation = Relation(type="The content of this resource references", value=value)
        result = relation.to_dataset_part_relation("Other")

        self.assertEqual(result.description, expected_description)
        if expected_url is None:
            self.assertIsNone(result.url)
        else:
            self.assertIsNotNone(result.url)
            self.assertEqual(str(result.url), expected_url)

    def test_is_part_of_relation_type(self):
        """A relation whose type ends with 'is part of' yields an IsPartOf schema object."""
        relation = Relation(
            type="The content of this resource is part of",
            value="Some collection, https://www.hydroshare.org/resource/abc123",
        )
        result = relation.to_dataset_part_relation("IsPartOf")
        self.assertEqual(str(result.url), "https://www.hydroshare.org/resource/abc123")
        self.assertIsInstance(result, schema.IsPartOf)
        self.assertEqual(result.description, "Some collection")

    def test_has_part_relation_type(self):
        """A relation whose type ends with 'resource includes' yields a HasPart schema object."""
        relation = Relation(
            type="This resource includes",
            value="A contained resource, https://www.hydroshare.org/resource/def456",
        )
        result = relation.to_dataset_part_relation("HasPart")
        self.assertEqual(str(result.url), "https://www.hydroshare.org/resource/def456")
        self.assertIsInstance(result, schema.HasPart)
        self.assertEqual(result.description, "A contained resource")

    def test_other_relation_type_sets_name(self):
        """Any relation_type other than HasPart or IsPartOf yields a Relation schema object with name set."""
        rel_type = "The content of this resource references"
        relation = Relation(type=rel_type, value="Some value")
        result = relation.to_dataset_part_relation("Other")
        self.assertIsInstance(result, schema.Relation)
        self.assertEqual(result.name, rel_type)
