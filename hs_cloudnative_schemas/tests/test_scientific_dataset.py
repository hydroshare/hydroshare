import unittest

from hs_cloudnative_schemas.schema.base import MediaObject, Organization
from hs_cloudnative_schemas.schema.dataset import AdditionalType, ScientificDataset
from hs_cloudnative_schemas.schema.datavariable import DataVariable

# Fields that must be omitted from the serialized output when they have no value
OMIT_WHEN_EMPTY = ("coordinates", "sourceOrganization", "associatedMedia")


def _validated_dataset(**kwargs):
    """Build a ScientificDataset the way the hs_extract raster/feature extractors do (full validation,
    without coordinates/sourceOrganization/associatedMedia)."""
    return ScientificDataset(
        variableMeasured=[],
        dimensions=[],
        additionalType=AdditionalType.GEOGRAPHIC_RASTER,
        **kwargs,
    )


class TestScientificDatasetSchemaOrgCompliance(unittest.TestCase):
    """Tests that ScientificDataset does not emit non schema.org compliant or always-empty fields."""

    def assert_empty_fields_omitted(self, dumped):
        for field_name in OMIT_WHEN_EMPTY:
            self.assertNotIn(field_name, dumped)

    def test_sharing_status_is_not_a_field(self):
        # creativeWorkStatus is the schema.org compliant field for the sharing status
        self.assertNotIn("sharing_status", ScientificDataset.model_fields)
        self.assertIn("creativeWorkStatus", ScientificDataset.model_fields)

    def test_omitted_fields_still_have_defaults(self):
        # removing the defaults would make validated construction (hs_extract) fail with 'Field required'
        for field_name in OMIT_WHEN_EMPTY:
            self.assertFalse(ScientificDataset.model_fields[field_name].is_required(), field_name)

    def test_validated_dataset_omits_empty_fields(self):
        for exclude_none in (False, True):
            with self.subTest(exclude_none=exclude_none):
                dumped = _validated_dataset().model_dump(by_alias=True, exclude_none=exclude_none)
                self.assert_empty_fields_omitted(dumped)

    def test_explicitly_empty_values_are_omitted(self):
        dataset = _validated_dataset(coordinates=[], associatedMedia=[], sourceOrganization=None)
        self.assert_empty_fields_omitted(dataset.model_dump(by_alias=True))

    def test_constructed_dataset_omits_empty_fields_but_keeps_json_ld_keys(self):
        # the adapter (hs_core/hydroshare_schemaorg_adapter.py) builds the dataset with model_construct
        dataset = ScientificDataset.model_construct()
        dataset.name = "A dataset"
        dumped = dataset.model_dump(by_alias=True)
        self.assert_empty_fields_omitted(dumped)
        self.assertTrue(dumped["@context"])
        self.assertEqual(dumped["@type"], "ScientificDataset")
        self.assertEqual(dumped["name"], "A dataset")

    def test_populated_fields_are_kept(self):
        # e.g., the NetCDF extractor populates coordinates
        dataset = _validated_dataset(
            coordinates=[DataVariable(name="lat", dimensions=["lat"])],
            associatedMedia=[MediaObject(contentUrl="https://example.com/file.nc", contentSize="1 KB", name="file.nc")],
            sourceOrganization=Organization(name="CUAHSI"),
        )
        for exclude_none in (False, True):
            with self.subTest(exclude_none=exclude_none):
                dumped = dataset.model_dump(by_alias=True, exclude_none=exclude_none)
                self.assertEqual(dumped["coordinates"][0]["name"], "lat")
                self.assertEqual(dumped["associatedMedia"][0]["name"], "file.nc")
                self.assertEqual(dumped["sourceOrganization"]["name"], "CUAHSI")

    def test_omission_is_per_field(self):
        # populating one field must not keep (or drop) the others
        dataset = _validated_dataset(coordinates=[DataVariable(name="lat", dimensions=["lat"])])
        dumped = dataset.model_dump(by_alias=True)
        self.assertEqual(dumped["coordinates"][0]["name"], "lat")
        self.assertNotIn("associatedMedia", dumped)
        self.assertNotIn("sourceOrganization", dumped)

    def test_json_serialization_omits_empty_fields(self):
        dumped_json = _validated_dataset().model_dump_json(by_alias=True)
        for field_name in OMIT_WHEN_EMPTY:
            self.assertNotIn(f'"{field_name}"', dumped_json)
