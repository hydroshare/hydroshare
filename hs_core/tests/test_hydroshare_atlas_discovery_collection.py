import json
from datetime import datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch

from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core.hydroshare_atlas_discovery_collection import MongoDBClient, collect_file_to_catalog, delete_file_from_catalog


SAMPLE_METADATA = {
    "name": "Test Resource",
    "description": "A test resource",
    "keywords": ["water", "hydrology"],
    "creator": [
        {"name": "Jane Smith", "@type": "Person"},
        {"name": "John Doe", "@type": "Person"},
    ],
    "dateCreated": "2026-01-15 10:30:00.000000+00:00",
}


def _make_s3_response(metadata: dict) -> dict:
    """Return a minimal mock S3 get_object response for the given metadata dict."""
    body = MagicMock()
    body.read.return_value = json.dumps(metadata).encode()
    return {"Body": body}


class TestCollectFileToCatalog(ParametrizedTestCase):

    def setUp(self):
        self.mock_s3 = MagicMock()
        self.mock_collection = MagicMock()

        self.s3_patcher = patch("hs_core.hydroshare_atlas_discovery_collection.s3", self.mock_s3)
        self.collection_patcher = patch.object(MongoDBClient, "get_discovery_collection", return_value=self.mock_collection)
        self.s3_patcher.start()
        self.collection_patcher.start()

    def tearDown(self):
        self.s3_patcher.stop()
        self.collection_patcher.stop()

    def test_create_document(self):
        """
        Calls collect_file_to_catalog with a typical metadata dict and asserts:
        - S3 get_object called with correct bucket/key
        - Document upserted into 'discovery' collection
        - _s3_filepath is set correctly
        - first_creator is set to first creator dict from metadata
        - dateCreated is parsed to datetime
        """
        metadata = {**SAMPLE_METADATA}
        self.mock_s3.get_object.return_value = _make_s3_response(SAMPLE_METADATA)
        filepath = "mybucket/res1/.hsjsonld/dataset_metadata.json"
        expected_bucket, expected_key = filepath.split("/", 1)
        collect_file_to_catalog(filepath)

        # Assert S3 call uses expected bucket and key
        self.mock_s3.get_object.assert_called_once_with(Bucket=expected_bucket, Key=expected_key)
        # Assert MongoDB upsert call uses expected filter and replacement document
        self.mock_collection.find_one_and_replace.assert_called_once()
        filter, replacement_metadata = self.mock_collection.find_one_and_replace.call_args[0]
        self.assertEqual(filter, {"_s3_filepath": expected_key})
        self.assertTrue(self.mock_collection.find_one_and_replace.call_args[1]["upsert"])
        self.assertEqual(replacement_metadata["_s3_filepath"], expected_key)
        self.assertEqual(replacement_metadata["first_creator"]["name"], metadata["creator"][0]["name"])
        self.assertEqual(replacement_metadata["dateCreated"], datetime.fromisoformat(metadata["dateCreated"]))

    @parametrize(
        "creator_field,expected_first_creator",
        [
            param(None, None, id="missing"),
            param([], None, id="empty_list"),
            param([{"@type": "Organization"}], {"@type": "Organization"}, id="no_name_field"),
            param([{"name": "  Jordan Rivers  "}], {"name": "Jordan Rivers"}, id="whitespace_stripping"),
        ],
    )
    def test_first_creator_edge_cases(self, creator_field, expected_first_creator):
        """Test first_creator handling with various edge cases."""
        metadata = {**SAMPLE_METADATA}
        if creator_field is None:
            metadata.pop("creator")
        else:
            metadata["creator"] = creator_field
        self.mock_s3.get_object.return_value = _make_s3_response(metadata)
        collect_file_to_catalog("bucket/res/.hsjsonld/dataset_metadata.json")
        _, replacement_metadata = self.mock_collection.find_one_and_replace.call_args[0]
        self.assertEqual(replacement_metadata["first_creator"], expected_first_creator)

    def test_replaced_resource_not_indexed(self):
        """Resource with 'replaced by newer version' relation should be skipped."""
        metadata = {
            **SAMPLE_METADATA,
            "relations": [
                {"name": "This resource has been replaced by a newer version", "value": "https://example.com"}
            ],
        }
        self.mock_s3.get_object.return_value = _make_s3_response(metadata)
        collect_file_to_catalog("bucket/res/.hsjsonld/dataset_metadata.json")
        self.mock_collection.find_one_and_replace.assert_not_called()


class TestDeleteFileFromCatalog(TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()

        self.collection_patcher = patch.object(MongoDBClient, "get_discovery_collection", return_value=self.mock_collection)
        self.collection_patcher.start()

    def tearDown(self):
        self.collection_patcher.stop()

    def test_delete_document(self):
        """Deletes document from discovery collection using object key (bucket prefix stripped)."""
        delete_file_from_catalog("userbucket/abc123/.hsjsonld/dataset_metadata.json")
        self.mock_collection.delete_one.assert_called_once_with(
            {"_s3_filepath": "abc123/.hsjsonld/dataset_metadata.json"}
        )
