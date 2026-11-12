import json
import unittest
from unittest import mock
from unittest_parametrize import ParametrizedTestCase, parametrize, param
from pydantic import ValidationError

from hs_cloudnative_schemas.schema import base as schema
from hs_core.hydroshare_schemaorg_adapter import Contributor, Creator, HydroshareMetadataAdapter, Relation
from hs_core.hydroshare.utils import current_site_url


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
            identifiers={"ORCID": "https://orcid.org/0000-0001-2345-6789", "Unknown": "https://example.com"},
        )
        result = creator.to_dataset_creator()

        # HydroShareID is a valid enum member (populated through a separate
        # mechanism, not from Party.identifiers) so it round-trips; "Unknown"
        # isn't a PersonIdentifierPropertyID member and is dropped.
        self.assertEqual(len(result.identifier), 1)
        self.assertEqual(result.identifier[0].propertyID, "ORCID")

    @mock.patch("hs_core.hydroshare.utils.current_site_url", return_value="https://www.hydroshare.org")
    def test_linked_hydroshare_user_gets_hydroshareid_identifier(self, _mock_site_url):
        creator = Creator(
            name="Jane Smith", identifiers={"ORCID": "https://orcid.org/0000-0001-2345-6789"},
            hydroshare_user_id=123
        )
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

    def test_named_creator_with_homepage_gets_person_url(self):
        creator = Creator(name="Jane Smith", homepage="https://example.com/jane")
        result = creator.to_dataset_creator()

        self.assertEqual(str(result.url), "https://example.com/jane")

    def test_named_contributor_without_homepage_has_no_person_url(self):
        contributor = Contributor(name="John Doe")
        result = contributor.to_dataset_contributor()

        self.assertFalse(getattr(result, "url", None))

    def test_org_only_party_homepage_stays_on_organization(self):
        creator = Creator(organization="Acme Hydrology", homepage="https://acme.example.com")
        result = creator.to_dataset_creator()

        self.assertEqual(result.name, "Acme Hydrology")
        self.assertEqual(str(result.url), "https://acme.example.com/")


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


class TestToCatalogRecordId(ParametrizedTestCase):
    """Tests that @id mirrors dataset.url: the DOI for published resources, the HydroShare URL otherwise."""

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
    def test_id_matches_url(self, sharing_status, is_doi):
        expected_id = (
            f"https://doi.org/10.4211/hs.{RESOURCE_ID}" if is_doi
            else f"{current_site_url()}/resource/{RESOURCE_ID}"
        )
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(str(dataset.id), expected_id)
        self.assertEqual(str(dataset.id), str(dataset.url))


class TestToCatalogRecordSameAs(ParametrizedTestCase):
    """Tests that sameAs is the HydroShare URL only for published resources (whose @id/url is the DOI)."""

    def test_published_has_hydroshare_url(self):
        metadata = {**MINIMAL_METADATA, "sharing_status": "published"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(str(dataset.sameAs), f"{current_site_url()}/resource/{RESOURCE_ID}")

    @parametrize(
        "sharing_status",
        [
            param("public", id="public"),
            param("private", id="private"),
            param("discoverable", id="discoverable"),
            param(None, id="no_sharing_status"),
        ],
    )
    def test_non_published_has_no_same_as(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.sameAs)


class TestToCatalogRecordIsAccessibleForFree(ParametrizedTestCase):
    """Tests that isAccessibleForFree is True for public and published resources, None otherwise."""

    @parametrize(
        "sharing_status",
        [
            param("public", id="public"),
            param("published", id="published"),
        ],
    )
    def test_public_and_published_are_accessible_for_free(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIs(dataset.isAccessibleForFree, True)

    @parametrize(
        "sharing_status",
        [
            param("private", id="private"),
            param("discoverable", id="discoverable"),
            param(None, id="no_sharing_status"),
        ],
    )
    def test_other_statuses_have_no_is_accessible_for_free(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.isAccessibleForFree)


class TestToCatalogRecordIdentifier(unittest.TestCase):
    """Tests the identifier list: HydroShare URL, DOI for published resources, and other metadata identifiers."""

    def test_published_has_doi_then_hydroshare_url(self):
        metadata = {**MINIMAL_METADATA, "sharing_status": "published"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.identifier), 2)
        doi_entry = dataset.identifier[0].model_dump(by_alias=True, exclude_none=True, mode="json")
        self.assertEqual(doi_entry, {
            "@id": f"https://doi.org/10.4211/hs.{RESOURCE_ID}",
            "@type": "PropertyValue",
            "propertyID": "https://registry.identifiers.org/registry/doi",
            "url": f"https://doi.org/10.4211/hs.{RESOURCE_ID}",
            "value": f"doi:10.4211/hs.{RESOURCE_ID}",
        })
        self.assertEqual(dataset.identifier[1], f"{current_site_url()}/resource/{RESOURCE_ID}")

    def test_non_published_has_only_hydroshare_url(self):
        metadata = {**MINIMAL_METADATA, "sharing_status": "public"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(dataset.identifier, [f"{current_site_url()}/resource/{RESOURCE_ID}"])


class TestToCatalogRecordPublisher(ParametrizedTestCase):
    """Tests that publisher is the CUAHSI Organization for published resources and None otherwise."""

    def test_published_has_cuahsi_organization(self):
        metadata = {**MINIMAL_METADATA, "sharing_status": "published"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsInstance(dataset.publisher, schema.PublisherOrganization)
        self.assertEqual(str(dataset.publisher.id), "https://ror.org/04s2bx355")
        self.assertEqual(
            dataset.publisher.name,
            "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)",
        )
        self.assertEqual(str(dataset.publisher.url), "https://www.cuahsi.org/")

    @parametrize(
        "sharing_status",
        [
            param("public", id="public"),
            param("private", id="private"),
            param("discoverable", id="discoverable"),
            param(None, id="no_sharing_status"),
        ],
    )
    def test_non_published_has_no_publisher(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.publisher)


class TestToCatalogRecordSubjectOf(unittest.TestCase):
    """Tests the subjectOf reference to the resource's Dublin Core XML metadata document."""

    def test_subject_of_references_dublin_core_xml(self):
        metadata = {**MINIMAL_METADATA}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.subjectOf), 1)
        subject_of = dataset.subjectOf[0]
        self.assertIsInstance(subject_of, schema.SubjectOf)
        self.assertEqual(subject_of.type, "DataDownload")
        self.assertEqual(subject_of.name, "resourcemetadata.xml")
        self.assertEqual(subject_of.description, "Dublin Core Metadata Document Describing the Dataset")
        self.assertEqual(str(subject_of.url), f"{current_site_url()}/hsapi/resource/{RESOURCE_ID}/scimeta/")
        self.assertEqual(subject_of.encodingFormat, "application/rdf+xml")


class TestToCatalogRecordIncludedInDataCatalog(ParametrizedTestCase):
    """Tests that includedInDataCatalog is the HydroShare DataCatalog when discoverable, None otherwise."""

    @parametrize(
        "sharing_status",
        [
            param("public", id="public"),
            param("published", id="published"),
            param("discoverable", id="discoverable"),
        ],
    )
    def test_discoverable_states_have_hydroshare_data_catalog(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsInstance(dataset.includedInDataCatalog, schema.DataCatalog)
        self.assertEqual(dataset.includedInDataCatalog.name, "HydroShare")
        self.assertEqual(str(dataset.includedInDataCatalog.url), "https://hydroshare.org/search/")

    @parametrize(
        "sharing_status",
        [
            param("private", id="private"),
            param(None, id="no_sharing_status"),
        ],
    )
    def test_non_discoverable_states_have_no_data_catalog(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.includedInDataCatalog)


class TestToCatalogRecordPublisher(ParametrizedTestCase):
    """Tests that publisher is the CUAHSI Organization for published resources and None otherwise."""
    def test_published_has_cuahsi_organization(self):
        metadata = {**MINIMAL_METADATA, "sharing_status": "published"}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsInstance(dataset.publisher, schema.PublisherOrganization)
        self.assertEqual(str(dataset.publisher.id), "https://ror.org/04s2bx355")
        self.assertEqual(
            dataset.publisher.name,
            "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)",
        )
        self.assertEqual(str(dataset.publisher.url), "https://www.cuahsi.org/")

    @parametrize(
        "sharing_status",
        [
            param("public", id="public"),
            param("private", id="private"),
            param("discoverable", id="discoverable"),
            param(None, id="no_sharing_status"),
        ],
    )
    def test_non_published_has_no_publisher(self, sharing_status):
        metadata = {**MINIMAL_METADATA, "sharing_status": sharing_status}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.publisher)


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


class TestToCatalogRecordAdditionalMetadata(unittest.TestCase):
    """Tests that hsmodels additional_metadata maps to schema.org additionalProperty."""

    def test_additional_metadata_maps_to_additional_property(self):
        metadata = {
            **MINIMAL_METADATA,
            "additional_metadata": {"site": "Logan River", "depth": "2 m"},
        }
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertEqual(len(dataset.additionalProperty), 2)
        for prop in dataset.additionalProperty:
            self.assertIsInstance(prop, schema.PropertyValue)
        self.assertEqual(
            {p.name: p.value for p in dataset.additionalProperty},
            {"site": "Logan River", "depth": "2 m"},
        )

    def test_empty_additional_metadata_yields_no_additional_property(self):
        metadata = {**MINIMAL_METADATA, "additional_metadata": {}}
        dataset = HydroshareMetadataAdapter.to_catalog_record(metadata, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.additionalProperty)

    def test_missing_additional_metadata_yields_no_additional_property(self):
        dataset = HydroshareMetadataAdapter.to_catalog_record(MINIMAL_METADATA, resource_id=RESOURCE_ID)
        self.assertIsNone(dataset.additionalProperty)

    def test_additional_metadata_key_not_in_dumped_record(self):
        metadata = {**MINIMAL_METADATA, "additional_metadata": {"site": "Logan River"}}
        dumped = HydroshareMetadataAdapter.to_catalog_record(
            metadata, resource_id=RESOURCE_ID
        ).model_dump(by_alias=True)
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
    "content_types": ["CompositeResource"],
}

# Keys that must never appear in the generated schema.org metadata
NON_COMPLIANT_KEYS = {"sharing_status", "review_started"}


def _generate_user_metadata(metadata):
    """Serialize the adapter output the same way hs_core.models.write_user_metadata_json_file does."""
    dataset = HydroshareMetadataAdapter.to_catalog_record(dict(metadata), resource_id=RESOURCE_ID)
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
