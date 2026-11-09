import json
import logging
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings
from botocore.exceptions import ClientError
from hsmodels.schemas.enums import RelationType
from unittest_parametrize import ParametrizedTestCase, parametrize, param

from hs_core.hydroshare_atlas_discovery_collection import (
    MongoDBClient, collect_file_to_catalog, delete_file_from_catalog, sync_resource_in_catalog
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


class TestSyncResourceInCatalog(ParametrizedTestCase):

    def setUp(self):
        self.mock_s3 = MagicMock()
        self.mock_collection = MagicMock()
        patcher_s3 = patch("hs_core.hydroshare_atlas_discovery_collection.s3", self.mock_s3)
        patcher_collection = patch.object(
            MongoDBClient, "get_discovery_collection", return_value=self.mock_collection
        )
        patcher_s3.start()
        patcher_collection.start()
        self.addCleanup(patcher_s3.stop)
        self.addCleanup(patcher_collection.stop)

    @staticmethod
    def _key(resource_id: str) -> str:
        return f"{resource_id}/.hsjsonld/dataset_metadata.json"

    def _serve_versions(self, *versions):
        """Serve a chain of (resource id, status) pairs, oldest first, linked by version relations."""
        objects = {}
        for index, (resource_id, status) in enumerate(versions):
            relations = []
            if index > 0:
                relations.append(_relation(REPLACES, versions[index - 1][0]))
            if index < len(versions) - 1:
                relations.append(_relation(REPLACED_BY, versions[index + 1][0]))
            objects[self._key(resource_id)] = {
                **SAMPLE_METADATA, "creativeWorkStatus": {"name": status}, "relation": relations,
            }
        self.mock_s3.get_object.side_effect = _s3_objects(objects)

    def _sync(self, resource_id: str, discoverable: bool):
        sync_resource_in_catalog(f"bucket/{self._key(resource_id)}", discoverable)

    def _indexed(self) -> list:
        return [call[0][0]["_s3_filepath"] for call in self.mock_collection.find_one_and_replace.call_args_list]

    def _deleted(self) -> list:
        return [call[0][0]["_s3_filepath"] for call in self.mock_collection.delete_one.call_args_list]

    def test_resource_without_versions_is_indexed(self):
        self.mock_s3.get_object.side_effect = _s3_objects({
            self._key("v1"): {**SAMPLE_METADATA, "creativeWorkStatus": {"name": "Public"}},
        })
        self._sync("v1", True)
        self.assertEqual(self._indexed(), [self._key("v1")])
        self.assertEqual(self._deleted(), [])

    def test_resource_without_versions_is_removed_when_not_discoverable(self):
        self.mock_s3.get_object.side_effect = _s3_objects({
            self._key("v1"): {**SAMPLE_METADATA, "creativeWorkStatus": {"name": "Private"}},
        })
        self._sync("v1", False)
        self.assertEqual(self._indexed(), [])
        self.assertEqual(self._deleted(), [self._key("v1")])

    def test_new_visible_version_replaces_previous_version(self):
        self._serve_versions(("v1", "Public"), ("v2", "Public"))
        self._sync("v2", True)
        self.assertEqual(self._indexed(), [self._key("v2")])
        self.assertEqual(self._deleted(), [self._key("v1")])

    @parametrize(
        "status",
        [
            param("Public", id="public"),
            param("Published", id="published"),
            param("Discoverable", id="discoverable"),
        ],
    )
    def test_visible_next_version_replaces_this_version(self, status):
        self._serve_versions(("v1", "Public"), ("v2", "Public"), ("v3", status))
        self._sync("v2", True)
        self.assertEqual(self._indexed(), [self._key("v3")])
        self.assertCountEqual(self._deleted(), [self._key("v1"), self._key("v2")])

    def test_private_next_version_leaves_this_version_in_catalog(self):
        self._serve_versions(("v1", "Public"), ("v2", "Public"), ("v3", "Private"))
        self._sync("v2", True)
        self.assertEqual(self._indexed(), [self._key("v2")])
        self.assertCountEqual(self._deleted(), [self._key("v1"), self._key("v3")])

    def test_private_resource_restores_visible_previous_version(self):
        self._serve_versions(("v1", "Public"), ("v2", "Private"))
        self._sync("v2", False)
        self.assertEqual(self._indexed(), [self._key("v1")])
        self.assertEqual(self._deleted(), [self._key("v2")])

    def test_private_resource_does_not_restore_private_previous_version(self):
        self._serve_versions(("v1", "Private"), ("v2", "Private"))
        self._sync("v2", False)
        self.assertEqual(self._indexed(), [])
        self.assertCountEqual(self._deleted(), [self._key("v1"), self._key("v2")])

    def test_replaced_private_resource_does_not_restore_previous_version(self):
        """The visible next version stays the only catalog entry, so the previous version is not restored."""
        self._serve_versions(("v1", "Public"), ("v2", "Private"), ("v3", "Public"))
        self._sync("v2", False)
        self.assertEqual(self._indexed(), [self._key("v3")])
        self.assertCountEqual(self._deleted(), [self._key("v1"), self._key("v2")])

    def test_missing_version_metadata_is_ignored(self):
        self._serve_versions(("v1", "Public"), ("v2", "Public"))
        served = self.mock_s3.get_object.side_effect

        def get_object(Bucket, Key):
            if Key == self._key("v1"):
                raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
            return served(Bucket=Bucket, Key=Key)
        self.mock_s3.get_object.side_effect = get_object

        self._sync("v2", True)
        self.assertEqual(self._indexed(), [self._key("v2")])
        self.assertEqual(self._deleted(), [])


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
