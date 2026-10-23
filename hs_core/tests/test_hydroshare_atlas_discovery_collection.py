import json
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.test import SimpleTestCase, override_settings
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core.hydroshare_atlas_discovery_collection import (
    MongoDBClient, collect_file_to_catalog, delete_file_from_catalog, find_live_metadata_file
)


ZONES_CONFIG = {
    "hydroshare": {"bucket_name": "resource"},
    "published": {"bucket_name": "published"},
    "ciroh": {"bucket_name": "ciroh"},
}


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


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code}}, "HeadObject")


@override_settings(RESOURCE_S3_ZONES_CONFIG=ZONES_CONFIG, RESOURCE_S3_DEFAULT_ZONE="hydroshare")
class TestZoneClients(SimpleTestCase):

    def setUp(self):
        self.default_client = MagicMock(name="default")
        self.zone_clients = {"published": MagicMock(name="published"), "ciroh": MagicMock(name="ciroh")}
        self.s3_patcher = patch("hs_core.hydroshare_atlas_discovery_collection.s3", self.default_client)
        self.make_client_patcher = patch(
            "hs_core.hydroshare_atlas_discovery_collection._make_s3_client",
            side_effect=lambda zone=None: self.zone_clients[zone],
        )
        self.collection_patcher = patch.object(MongoDBClient, "get_discovery_collection", return_value=MagicMock())
        self.s3_patcher.start()
        self.make_client_patcher.start()
        self.collection_patcher.start()

    def tearDown(self):
        self.s3_patcher.stop()
        self.make_client_patcher.stop()
        self.collection_patcher.stop()

    def test_collect_reads_non_default_zone_bucket_with_its_zone_client(self):
        """A ciroh bucket object is read with the ciroh zone client, not the default-zone client."""
        self.zone_clients["ciroh"].get_object.return_value = _make_s3_response(SAMPLE_METADATA)
        collect_file_to_catalog("ciroh/res1/.hsjsonld/dataset_metadata.json")
        self.zone_clients["ciroh"].get_object.assert_called_once_with(
            Bucket="ciroh", Key="res1/.hsjsonld/dataset_metadata.json"
        )
        self.default_client.get_object.assert_not_called()

    def test_collect_reads_default_zone_bucket_with_default_client(self):
        """A default-zone bucket object is read with the default client."""
        self.default_client.get_object.return_value = _make_s3_response(SAMPLE_METADATA)
        collect_file_to_catalog("resource/res1/.hsjsonld/dataset_metadata.json")
        self.default_client.get_object.assert_called_once()

    def test_find_live_returns_other_bucket_holding_the_object(self):
        """Old bucket is excluded; the bucket where the object still exists is returned."""
        self.zone_clients["published"].head_object.side_effect = _client_error("404")
        key = "res1/.hsjsonld/dataset_metadata.json"
        self.assertEqual(find_live_metadata_file(key, exclude_bucket="resource"), f"ciroh/{key}")
        self.default_client.head_object.assert_not_called()
        self.zone_clients["ciroh"].head_object.assert_called_once_with(Bucket="ciroh", Key=key)

    def test_find_live_returns_none_when_no_other_bucket_has_object(self):
        """No other bucket has the object; should return None."""
        self.zone_clients["published"].head_object.side_effect = _client_error("404")
        self.zone_clients["ciroh"].head_object.side_effect = _client_error("NoSuchKey")
        self.assertIsNone(find_live_metadata_file("res1/.hsjsonld/dataset_metadata.json", exclude_bucket="resource"))

    def test_find_live_reraises_non_not_found_errors(self):
        """Access/server errors must propagate so the task retries instead of deleting the doc."""
        self.zone_clients["published"].head_object.side_effect = _client_error("403")
        with self.assertRaises(ClientError):
            find_live_metadata_file("res1/.hsjsonld/dataset_metadata.json", exclude_bucket="resource")
