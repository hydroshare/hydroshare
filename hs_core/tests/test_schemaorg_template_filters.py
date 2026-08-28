import json
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from hs_core.templatetags.hydroshare_tags import (
    creator_json_ld_element,
    first_relation_value_for_types,
    provenance_trace_json,
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
