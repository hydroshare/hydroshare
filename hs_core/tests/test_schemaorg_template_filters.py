import json
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from hs_core.templatetags.hydroshare_tags import (
    creator_json_ld_element,
    first_relation_value_for_types,
    provenance_trace_json,
    resource_files_json_ld,
    schemaorg_contact_point_json,
)


class TestSchemaorgTemplateFilters(SimpleTestCase):
    def test_creator_json_ld_element_emits_identifier_and_same_as(self):
        creators = [
            {
                "name": "Doe, Jane",
                "organization": "USU",
                "email": "jane@example.com",
                "address": "123 Main St",
                "relative_uri": "/user/123/",
                "homepage": "https://example.com/jane",
                "identifiers": {
                    "ORCID": "https://orcid.org/0000-0002-1825-0097",
                },
            }
        ]

        payload = json.loads(creator_json_ld_element(creators))
        creator = payload["@list"][0]

        self.assertEqual(creator["identifier"], "https://orcid.org/0000-0002-1825-0097")
        self.assertEqual(creator["sameAs"], "https://orcid.org/0000-0002-1825-0097")

    def test_schemaorg_contact_point_json_uses_first_ordered_creator(self):
        creators = [
            {
                "name": "Second Person",
                "organization": "Org B",
                "email": "second@example.com",
                "phone": "555-1111",
                "relative_uri": "/user/2/",
                "homepage": "https://example.com/second",
                "order": 2,
                "identifiers": {
                    "ORCID": "https://orcid.org/0000-0002-0000-0002",
                },
            },
            {
                "name": "First Person",
                "organization": "Org A",
                "email": "first@example.com",
                "phone": "555-0000",
                "relative_uri": "/user/1/",
                "homepage": "https://example.com/first",
                "order": 1,
                "identifiers": {
                    "ORCID": "https://orcid.org/0000-0001-0000-0001",
                },
            },
        ]

        contact_point = json.loads(schemaorg_contact_point_json(creators))

        self.assertEqual(contact_point["name"], "First Person")
        self.assertEqual(contact_point["email"], "first@example.com")
        self.assertEqual(contact_point["telephone"], "555-0000")
        self.assertEqual(contact_point["identifier"], "https://orcid.org/0000-0001-0000-0001")
        self.assertEqual(contact_point["sameAs"], "https://orcid.org/0000-0001-0000-0001")
        self.assertIn("https://www.hydroshare.org/user/1/", contact_point["url"])

    def test_first_relation_value_for_types_prefers_requested_order(self):
        relations = [
            {"type": "isVersionOf", "value": "https://example.com/version"},
            {"type": "source", "value": "https://example.com/source"},
        ]

        self.assertEqual(
            first_relation_value_for_types(relations, "source,isVersionOf"),
            "https://example.com/source",
        )
        self.assertEqual(
            first_relation_value_for_types(relations, "isVersionOf,source"),
            "https://example.com/version",
        )

    def test_provenance_trace_json_keeps_lineage_relations_only(self):
        relations = [
            {"type": "source", "value": "https://example.com/source"},
            {"type": "isVersionOf", "value": "https://example.com/version"},
            {"type": "references", "value": "https://example.com/reference"},
        ]

        trace_values = json.loads(provenance_trace_json(relations))

        self.assertEqual(
            trace_values,
            [
                "https://example.com/source",
                "https://example.com/version",
            ],
        )


class TestResourceFilesJsonLd(SimpleTestCase):
    def _make_resource(self, files_data):
        """Return a mock resource whose .files.all() yields simple file mocks."""
        file_mocks = []
        for name, mime in files_data:
            f = MagicMock()
            f.file_name = name
            f.mime_type = mime
            file_mocks.append(f)

        resource = MagicMock()
        resource.files.all.return_value = file_mocks
        return resource

    def test_emits_media_object_with_name_and_encoding_format(self):
        resource = self._make_resource([("data.csv", "text/csv")])
        entries = json.loads(resource_files_json_ld(resource))

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["@type"], "MediaObject")
        self.assertEqual(entries[0]["name"], "data.csv")
        self.assertEqual(entries[0]["encodingFormat"], "text/csv")

    def test_emits_multiple_files(self):
        resource = self._make_resource([
            ("report.pdf", "application/pdf"),
            ("data.nc", "application/x-netcdf"),
            ("readme.txt", "text/plain"),
        ])
        entries = json.loads(resource_files_json_ld(resource))

        self.assertEqual(len(entries), 3)
        names = [e["name"] for e in entries]
        self.assertIn("report.pdf", names)
        self.assertIn("data.nc", names)
        self.assertIn("readme.txt", names)

    def test_omits_encoding_format_when_mime_type_is_none(self):
        resource = self._make_resource([("archive.zip", None)])
        entries = json.loads(resource_files_json_ld(resource))

        self.assertEqual(len(entries), 1)
        self.assertNotIn("encodingFormat", entries[0])
        self.assertEqual(entries[0]["name"], "archive.zip")

    def test_returns_empty_string_for_resource_with_no_files(self):
        resource = self._make_resource([])
        result = resource_files_json_ld(resource)

        self.assertEqual(result, "")
