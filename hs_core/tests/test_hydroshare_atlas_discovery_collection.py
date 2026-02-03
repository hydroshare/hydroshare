import copy
import io
import json
from unittest import mock

from django.test import TestCase

from hs_core import hydroshare_atlas_discovery_collection as collector
from hs_core.enums import RelationTypes
from hs_core.models import Relation


class _MockBody(io.BytesIO):
    """Wrapper so mocked S3 responses expose .read()."""

    def __init__(self, payload: dict):
        super().__init__(json.dumps(payload).encode("utf-8"))


class _MockS3:
    def __init__(self, objects: dict[str, dict]):
        self.objects = objects
        self.calls = []

    def get_object(self, Bucket: str, Key: str):
        self.calls.append((Bucket, Key))
        if Key not in self.objects:
            raise AssertionError(f"Unexpected S3 key requested: {Key}")
        return {"Body": _MockBody(self.objects[Key])}


class _MockCollection:
    def __init__(self):
        self.replaced = None

    def find_one_and_replace(self, filter: dict, doc: dict, upsert: bool = False):
        self.replaced = {
            "filter": copy.deepcopy(filter),
            "doc": copy.deepcopy(doc),
            "upsert": upsert,
        }


class _MockDB:
    def __init__(self, collection: _MockCollection):
        self.collection = collection

    def __getitem__(self, name: str):
        if name != "discovery":
            raise AssertionError(f"Unexpected collection requested: {name}")
        return self.collection


class HydroshareAtlasDiscoveryCollectionTests(TestCase):
    def test_sets_first_creator_and_rewrites_urls(self):
        bucket = "test-bucket"
        resource_id = "res-123"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        filepath = f"{bucket}/{dataset_key}"

        metadata = {
            "identifier": [f"https://example.org/resource/{resource_id}"],
            "url": f"https://example.org/resource/{resource_id}",
            "creator": [{"name": "Alice"}, {"name": "Bob"}],
            "relations": [],
            "hasPart": [{"url": f"https://files.test/{bucket}/{resource_id}/.hsjsonld/part.json"}],
        }

        mock_s3 = _MockS3({dataset_key: metadata, f"{resource_id}/.hsjsonld/part.json": {"additionalType": "Document"}})
        mock_collection = _MockCollection()
        site_url = collector.hs_utils.current_site_url()

        with mock.patch.object(collector, "s3", mock_s3), \
                mock.patch.object(collector, "hydroshare_atlas_db", _MockDB(mock_collection)):
            collector.collect_file_to_catalog(filepath)

        stored = mock_collection.replaced["doc"]
        self.assertEqual(mock_collection.replaced["filter"], {"_s3_filepath": filepath})
        self.assertEqual(stored["_s3_filepath"], filepath)
        self.assertEqual(stored["url"], f"{site_url}/resource/{resource_id}")
        self.assertEqual(stored["identifier"][0], f"{site_url}/resource/{resource_id}")
        self.assertEqual(stored["first_creator"], {"name": "Alice"})

    def test_preserves_version_relation(self):
        bucket = "test-bucket"
        resource_id = "res-123"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        filepath = f"{bucket}/{dataset_key}"

        version_label = dict(Relation.SOURCE_TYPES)[RelationTypes.isVersionOf.value]
        metadata = {
            "identifier": [f"https://example.org/resource/{resource_id}"],
            "url": f"https://example.org/resource/{resource_id}",
            "creator": [{"name": "Alice"}],
            "relations": [{"name": version_label, "description": "old version"}],
            "hasPart": [{"url": f"https://files.test/{bucket}/{resource_id}/.hsjsonld/part.json"}],
        }

        mock_s3 = _MockS3({dataset_key: metadata, f"{resource_id}/.hsjsonld/part.json": {"additionalType": "Document"}})
        mock_collection = _MockCollection()

        with mock.patch.object(collector, "s3", mock_s3), \
                mock.patch.object(collector, "hydroshare_atlas_db", _MockDB(mock_collection)):
            collector.collect_file_to_catalog(filepath)

        stored = mock_collection.replaced["doc"]
        self.assertIn(version_label, [rel.get("name") for rel in stored.get("relations", [])])

    def test_skips_resource_replaced_by_newer_version(self):
        bucket = "test-bucket"
        resource_id = "res-123"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        filepath = f"{bucket}/{dataset_key}"

        metadata = {
            "identifier": [f"https://example.org/resource/{resource_id}"],
            "url": f"https://example.org/resource/{resource_id}",
            "creator": [{"name": "Alice"}],
            "relations": [{"name": "This resource has been replaced by a newer version", "description": "obsolete"}],
        }

        mock_s3 = _MockS3({dataset_key: metadata})
        mock_collection = _MockCollection()

        with mock.patch.object(collector, "s3", mock_s3), \
                mock.patch.object(collector, "hydroshare_atlas_db", _MockDB(mock_collection)):
            collector.collect_file_to_catalog(filepath)

        self.assertIsNone(
            mock_collection.replaced,
            "replaced-by-newer-version resources must not be written to the catalog",
        )

    def test_content_types_from_haspart_includes_missing_additional_type(self):
        bucket = "test-bucket"
        resource_id = "res-abc"
        dataset_key = f"{resource_id}/.hsjsonld/dataset_metadata.json"
        filepath = f"{bucket}/{dataset_key}"

        has_parts = [
            {"url": f"https://files.test/{bucket}/{resource_id}/.hsjsonld/part-a.json"},
            {"url": f"https://files.test/{bucket}/{resource_id}/.hsjsonld/part-b.json"},
        ]
        metadata = {
            "identifier": ["id"],
            "url": "url",
            "creator": [{"name": "first"}],
            "hasPart": has_parts,
        }

        mock_s3 = _MockS3(
            {
                dataset_key: metadata,
                f"{resource_id}/.hsjsonld/part-a.json": {"additionalType": "Raster"},
                f"{resource_id}/.hsjsonld/part-b.json": {},
            }
        )
        mock_collection = _MockCollection()

        with mock.patch.object(collector, "s3", mock_s3), \
                mock.patch.object(collector, "hydroshare_atlas_db", _MockDB(mock_collection)):
            collector.collect_file_to_catalog(filepath)

        stored_types = mock_collection.replaced["doc"]["content_types"]

        self.assertCountEqual(stored_types, ["Raster", None])
        self.assertCountEqual(
            mock_s3.calls,
            [
                (bucket, dataset_key),
                (bucket, f"{resource_id}/.hsjsonld/part-a.json"),
                (bucket, f"{resource_id}/.hsjsonld/part-b.json"),
            ],
        )
