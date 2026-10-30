import json
import logging
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from hsmodels.schemas.enums import RelationType
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core.hydroshare_atlas_discovery_collection import (
    MongoDBClient, collect_file_to_catalog, delete_file_from_catalog
)


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


REPLACED_BY = RelationType.isReplacedBy.value
REPLACES = RelationType.isVersionOf.value


def _s3_objects(objects: dict):
    """Return a get_object side effect serving the given {object key: metadata} mapping."""
    def get_object(Bucket, Key):
        return _make_s3_response(objects[Key])
    return get_object


def _relation(name: str, resource_id: str) -> dict:
    return {"name": name, "description": "citation",
            "url": f"https://www.hydroshare.org/resource/{resource_id}/"}


class TestCollectFileToCatalog(ParametrizedTestCase):

    def setUp(self):
        self.mock_s3 = MagicMock()
        self.mock_collection = MagicMock()

        self.s3_patcher = patch("hs_core.hydroshare_atlas_discovery_collection.s3", self.mock_s3)
        self.collection_patcher = patch.object(
            MongoDBClient,
            "get_discovery_collection",
            return_value=self.mock_collection
        )
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

    @parametrize(
        "key,value,expected",
        [
            param("dateCreated", "2026-01-15 10:30:00.000000+00:00",
                  datetime(2026, 1, 15, 10, 30, tzinfo=timezone.utc), id="legacy_space_separator_with_offset"),
            param("endDate", "2016-03-06 00:50:50",
                  datetime(2016, 3, 6, 0, 50, 50), id="legacy_temporal_coverage_no_offset"),
            param("datePublished", "2016-03-06T00:50:50.652782+00:00",
                  datetime(2016, 3, 6, 0, 50, 50, 652782, tzinfo=timezone.utc), id="iso_t_separator_with_offset"),
            param("name", "2016-03-06T00:50:50.652782+00:00",
                  "2016-03-06T00:50:50.652782+00:00", id="non_date_key_left_as_string"),
            param("dateModified", "not a date", "not a date", id="unparseable_value_left_as_string"),
        ],
    )
    def test_datetime_parsing_by_key(self, key, value, expected):
        """Date keys are converted via fromisoformat for legacy and ISO formats; other keys are untouched."""
        metadata = {**SAMPLE_METADATA, key: value}
        self.mock_s3.get_object.return_value = _make_s3_response(metadata)
        collect_file_to_catalog("bucket/res/.hsjsonld/dataset_metadata.json")
        _, replacement_metadata = self.mock_collection.find_one_and_replace.call_args[0]
        self.assertEqual(replacement_metadata[key], expected)

    def test_nested_temporal_coverage_dates_parsed(self):
        """startDate/endDate nested inside temporalCoverage are converted to datetime."""
        metadata = {
            **SAMPLE_METADATA,
            "temporalCoverage": {
                "startDate": "2016-03-06 00:00:00",
                "endDate": "2016-03-07T12:00:00.000000+00:00",
            },
        }
        self.mock_s3.get_object.return_value = _make_s3_response(metadata)
        collect_file_to_catalog("bucket/res/.hsjsonld/dataset_metadata.json")
        _, replacement_metadata = self.mock_collection.find_one_and_replace.call_args[0]
        temporal = replacement_metadata["temporalCoverage"]
        self.assertEqual(temporal["startDate"], datetime(2016, 3, 6))
        self.assertEqual(temporal["endDate"], datetime(2016, 3, 7, 12, 0, 0, tzinfo=timezone.utc))

    @parametrize(
        "status",
        [
            param("Public", id="public"),
            param("Published", id="published"),
            param("Discoverable", id="discoverable"),
        ],
    )
    def test_replaced_resource_removed_when_newer_version_visible(self, status):
        """A replaced resource is removed from the collection, not re-indexed, if its newer version is in the collection and visible."""
        old_version = {**SAMPLE_METADATA, "relation": [_relation(REPLACED_BY, "new-version")]}
        self.mock_s3.get_object.side_effect = _s3_objects({
            "old-version/.hsjsonld/dataset_metadata.json": old_version,
        })
        self.mock_collection.find_one.return_value = {"creativeWorkStatus": {"name": status}}
        collect_file_to_catalog("bucket/old-version/.hsjsonld/dataset_metadata.json")
        self.mock_collection.find_one_and_replace.assert_not_called()
        self.mock_collection.delete_one.assert_called_once_with(
            {"_s3_filepath": "old-version/.hsjsonld/dataset_metadata.json"}
        )

    def test_replaced_resource_indexed_when_newer_version_private(self):
        """A replaced resource stays in the collection while its newer version is private."""
        old_version = {**SAMPLE_METADATA, "relation": [_relation(REPLACED_BY, "new-version")]}
        self.mock_s3.get_object.side_effect = _s3_objects({
            "old-version/.hsjsonld/dataset_metadata.json": old_version,
        })
        self.mock_collection.find_one.return_value = {"creativeWorkStatus": {"name": "Private"}}
        collect_file_to_catalog("bucket/old-version/.hsjsonld/dataset_metadata.json")
        self.mock_collection.find_one_and_replace.assert_called_once()

    def test_replaced_resource_indexed_when_newer_version_not_in_collection(self):
        """A replaced resource stays in the collection while its newer version is not in the collection."""
        old_version = {**SAMPLE_METADATA, "relation": [_relation(REPLACED_BY, "new-version")]}
        self.mock_s3.get_object.side_effect = _s3_objects({
            "old-version/.hsjsonld/dataset_metadata.json": old_version,
        })
        self.mock_collection.find_one.return_value = None
        collect_file_to_catalog("bucket/old-version/.hsjsonld/dataset_metadata.json")
        self.mock_collection.find_one_and_replace.assert_called_once()

    def test_replaces_relation_removes_previous_version_when_visible(self):
        """A public newer version removes the resource it replaces from the collection."""
        new_version = {**SAMPLE_METADATA, "relation": [_relation(REPLACES, "old-version")],
                       "creativeWorkStatus": {"name": "Public"}}
        self.mock_s3.get_object.side_effect = _s3_objects({
            "new-version/.hsjsonld/dataset_metadata.json": new_version,
        })
        collect_file_to_catalog("bucket/new-version/.hsjsonld/dataset_metadata.json")
        self.mock_collection.find_one_and_replace.assert_called_once()
        self.mock_collection.delete_one.assert_called_once_with(
            {"_s3_filepath": "old-version/.hsjsonld/dataset_metadata.json"}
        )

    def test_replaces_relation_keeps_previous_version_when_private(self):
        """A private newer version leaves the resource it replaces in the collection."""
        new_version = {**SAMPLE_METADATA, "relation": [_relation(REPLACES, "old-version")],
                       "creativeWorkStatus": {"name": "Private"}}
        self.mock_s3.get_object.side_effect = _s3_objects({
            "new-version/.hsjsonld/dataset_metadata.json": new_version,
        })
        collect_file_to_catalog("bucket/new-version/.hsjsonld/dataset_metadata.json")
        self.mock_collection.delete_one.assert_not_called()


class TestDeleteFileFromCatalog(TestCase):

    def setUp(self):
        self.mock_collection = MagicMock()

        self.collection_patcher = patch.object(
            MongoDBClient,
            "get_discovery_collection",
            return_value=self.mock_collection
        )
        self.collection_patcher.start()

    def tearDown(self):
        self.collection_patcher.stop()

    def test_delete_document(self):
        """Deletes document from discovery collection using object key (bucket prefix stripped)."""
        delete_file_from_catalog("userbucket/abc123/.hsjsonld/dataset_metadata.json")
        self.mock_collection.delete_one.assert_called_once_with(
            {"_s3_filepath": "abc123/.hsjsonld/dataset_metadata.json"}
        )

    def test_delete_logs_call_and_result(self):
        """Each delete call logs its invocation and the number of documents removed."""
        self.mock_collection.delete_one.return_value.deleted_count = 1
        # test settings disable logging globally; re-enable it for this assertion only
        previous_disable_level = logging.root.manager.disable
        logging.disable(logging.NOTSET)
        self.addCleanup(logging.disable, previous_disable_level)
        with self.assertLogs("hs_core.hydroshare_atlas_discovery_collection", level="INFO") as logs:
            delete_file_from_catalog("userbucket/abc123/.hsjsonld/dataset_metadata.json")
        self.assertTrue(any("delete_file_from_catalog called for" in m for m in logs.output))
        self.assertTrue(any("removed 1 document(s)" in m for m in logs.output))
