import json

from hsextract import main as main_module
from hsextract.content_types.models import BaseMetadataObject
from hsextract.content_types.raster.models import RasterMetadataObject
from hsextract.utils import s3 as s3_utils


class _FakePaginator:
    def __init__(self, pages, expected_prefix):
        self._pages = pages
        self._expected_prefix = expected_prefix

    def paginate(self, Bucket, Prefix):
        assert Bucket == "test-bucket"
        assert Prefix == self._expected_prefix
        return self._pages


class _FakeS3Client:
    def __init__(self, pages, expected_prefix="resource/data/contents"):
        self._pages = pages
        self._expected_prefix = expected_prefix
        self.uploaded = None

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return _FakePaginator(self._pages, self._expected_prefix)

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
        self.uploaded = {
            "bucket": bucket,
            "key": key,
            "extra_args": ExtraArgs,
            "body": fileobj.read().decode("utf-8")
        }


def test_write_file_manifest_streams_json_array(monkeypatch):
    pages = [
        {
            "Contents": [
                {
                    "Key": "resource/data/contents/a.txt",
                    "Size": 1000,
                    "ETag": '"abc"'
                },
                {
                    "Key": "resource/data/contents/b.csv",
                    "Size": 2500,
                    "ETag": '"def"'
                }
            ]
        }
    ]
    fake_client = _FakeS3Client(pages)

    monkeypatch.setattr(s3_utils, "s3_client", fake_client)
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")
    monkeypatch.setenv("HS_EXTRACT_JSON_SPOOL_MAX_SIZE", "32")

    manifest_reference = s3_utils.write_file_manifest(
        "test-bucket/resource/data/contents",
        "test-bucket/resource/.hsjsonld/file_manifest.json",
        enabled=True
    )

    assert fake_client.uploaded["bucket"] == "test-bucket"
    assert fake_client.uploaded["key"] == "resource/.hsjsonld/file_manifest.json"
    assert fake_client.uploaded["extra_args"] == {"ContentType": "application/json"}

    manifest_json = json.loads(fake_client.uploaded["body"])
    assert len(manifest_json) == 2
    assert manifest_json[0]["name"] == "a.txt"
    assert manifest_json[0]["contentUrl"] == "https://s3.example.org/test-bucket/resource/data/contents/a.txt"
    assert manifest_json[1]["name"] == "b.csv"
    assert manifest_reference["name"] == "file_manifest.json"
    assert manifest_reference["encodingFormat"] == "application/json"
    assert manifest_reference["contentUrl"] == "https://s3.example.org/test-bucket/resource/.hsjsonld/file_manifest.json"


def test_write_has_part_file_streams_json_array(monkeypatch):
    fake_client = _FakeS3Client([])

    monkeypatch.setattr(s3_utils, "s3_client", fake_client)
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")
    monkeypatch.setenv("HS_EXTRACT_JSON_SPOOL_MAX_SIZE", "32")

    has_part_reference = s3_utils.write_has_part_file(
        "test-bucket/resource/.hsjsonld/has_parts.json",
        iter([
            {"url": "https://example.com/part-1", "name": "Part 1"},
            {"url": "https://example.com/part-2"},
        ]),
    )

    assert fake_client.uploaded["bucket"] == "test-bucket"
    assert fake_client.uploaded["key"] == "resource/.hsjsonld/has_parts.json"
    assert fake_client.uploaded["extra_args"] == {"ContentType": "application/json"}

    uploaded_json = json.loads(fake_client.uploaded["body"])
    assert uploaded_json == [
        {"url": "https://example.com/part-1", "name": "Part 1"},
        {"url": "https://example.com/part-2"},
    ]
    assert has_part_reference["type"] == "CreativeWork"
    assert str(has_part_reference["url"]) == "https://s3.example.org/test-bucket/resource/.hsjsonld/has_parts.json"


def test_iter_find_yields_keys_lazily(monkeypatch):
    pages = [
        {
            "Contents": [
                {"Key": "resource/.hsjsonld/a.json"},
                {"Key": "resource/.hsjsonld/b.json"},
            ]
        },
        {
            "Contents": [
                {"Key": "resource/.hsjsonld/c.json"},
            ]
        },
    ]
    fake_client = _FakeS3Client(pages, expected_prefix="resource/.hsjsonld")

    monkeypatch.setattr(s3_utils, "s3_client", fake_client)

    found_keys = list(s3_utils.iter_find("test-bucket/resource/.hsjsonld"))

    assert found_keys == [
        "test-bucket/resource/.hsjsonld/a.json",
        "test-bucket/resource/.hsjsonld/b.json",
        "test-bucket/resource/.hsjsonld/c.json",
    ]


def test_retrieve_file_manifest_remains_list_based(monkeypatch):
    pages = [
        {
            "Contents": [
                {
                    "Key": "resource/data/contents/a.txt",
                    "Size": 1000,
                    "ETag": '"abc"'
                }
            ]
        }
    ]
    fake_client = _FakeS3Client(pages)

    monkeypatch.setattr(s3_utils, "s3_client", fake_client)
    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")

    manifest = s3_utils.retrieve_file_manifest(
        "test-bucket/resource/data/contents",
        enabled=True
    )

    assert isinstance(manifest, list)
    assert len(manifest) == 1
    assert manifest[0]["name"] == "a.txt"


def test_write_resource_jsonld_metadata_writes_file_manifest(monkeypatch):
    calls = {}

    class _DummyMetadataObject:
        system_metadata_path = "test-bucket/resource/.hsmetadata/system_metadata.json"
        user_metadata_path = "test-bucket/resource/.hsmetadata/user_metadata.json"
        resource_contents_path = "test-bucket/resource/data/contents"
        resource_md_jsonld_path = "test-bucket/resource/.hsjsonld"
        resource_associated_media_jsonld_path = "test-bucket/resource/.hsjsonld/file_manifest.json"
        resource_has_parts_jsonld_path = "test-bucket/resource/.hsjsonld/has_parts.json"
        resource_metadata_jsonld_path = "test-bucket/resource/.hsjsonld/dataset_metadata.json"
        resource_metadata_status_jsonld_path = "test-bucket/resource/.hsjsonld/resource_metadata_status.json"
        resource_associated_media = [{"name": "a.txt"}]

    def _fake_load_metadata(path):
        if path.endswith("system_metadata.json"):
            return {"title": "system", "hasPart": [{"url": "system-part"}]}
        return {"description": "user", "hasPart": [{"url": "user-part"}]}

    def _fake_write_file_manifest(resource_root_path, manifest_path, enabled=False):
        calls["manifest"] = {
            "resource_root_path": resource_root_path,
            "manifest_path": manifest_path,
            "enabled": enabled,
        }
        return {
            "name": "file_manifest.json",
            "contentUrl": "https://s3.example.org/test-bucket/resource/.hsjsonld/file_manifest.json",
            "contentSize": "0.1 KB",
            "encodingFormat": "application/json",
        }

    def _fake_write_has_part_file(parts_path, has_parts):
        calls["has_part"] = {
            "parts_path": parts_path,
            "has_parts": list(has_parts),
        }
        return {
            "url": "https://s3.example.org/test-bucket/resource/.hsjsonld/has_parts.json",
            "type": "CreativeWork",
        }

    def _fake_write_metadata(metadata_path, metadata_json):
        calls["metadata"] = {
            "metadata_path": metadata_path,
            "metadata_json": metadata_json,
        }

    monkeypatch.setattr(main_module, "load_metadata", _fake_load_metadata)
    monkeypatch.setattr(main_module, "iter_find", lambda path: iter(()))
    monkeypatch.setattr(main_module, "write_file_manifest", _fake_write_file_manifest)
    monkeypatch.setattr(main_module, "write_has_part_file", _fake_write_has_part_file)
    monkeypatch.setattr(main_module, "write_metadata", _fake_write_metadata)

    main_module.write_resource_jsonld_metadata(_DummyMetadataObject())

    assert calls["manifest"] == {
        "resource_root_path": "test-bucket/resource/data/contents",
        "manifest_path": "test-bucket/resource/.hsjsonld/file_manifest.json",
        "enabled": True,
    }
    assert calls["has_part"] == {
        "parts_path": "test-bucket/resource/.hsjsonld/has_parts.json",
        "has_parts": [
            {"url": "system-part"},
            {"url": "user-part"},
        ],
    }
    assert calls["metadata"]["metadata_path"] == "test-bucket/resource/.hsjsonld/dataset_metadata.json"
    assert calls["metadata"]["metadata_json"]["associatedMedia"] == [{
        "name": "file_manifest.json",
        "contentUrl": "https://s3.example.org/test-bucket/resource/.hsjsonld/file_manifest.json",
        "contentSize": "0.1 KB",
        "encodingFormat": "application/json",
    }]
    assert calls["metadata"]["metadata_json"]["hasPart"] == [
        {
            "url": "https://s3.example.org/test-bucket/resource/.hsjsonld/has_parts.json",
            "type": "CreativeWork",
        },
    ]


def test_write_resource_jsonld_metadata_skips_manifest_rebuild(monkeypatch):
    calls = {}

    class _DummyMetadataObject:
        system_metadata_path = "test-bucket/resource/.hsmetadata/system_metadata.json"
        user_metadata_path = "test-bucket/resource/.hsmetadata/user_metadata.json"
        resource_contents_path = "test-bucket/resource/data/contents"
        resource_md_jsonld_path = "test-bucket/resource/.hsjsonld"
        resource_associated_media_jsonld_path = "test-bucket/resource/.hsjsonld/file_manifest.json"
        resource_has_parts_jsonld_path = "test-bucket/resource/.hsjsonld/has_parts.json"
        resource_metadata_jsonld_path = "test-bucket/resource/.hsjsonld/dataset_metadata.json"
        resource_metadata_status_jsonld_path = "test-bucket/resource/.hsjsonld/resource_metadata_status.json"

    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")
    monkeypatch.setattr(main_module, "load_metadata", lambda path: {"title": "metadata"})
    monkeypatch.setattr(main_module, "iter_find", lambda path: iter(()))
    monkeypatch.setattr(main_module, "write_has_part_file", lambda parts_path, has_parts: {"url": "parts"})
    monkeypatch.setattr(main_module, "write_file_manifest", lambda *args, **kwargs: calls.setdefault("manifest_called", True))
    monkeypatch.setattr(main_module, "complete_manifest_rebuild", lambda path: calls.setdefault("completed", path))

    def _fake_write_metadata(metadata_path, metadata_json):
        calls["metadata_path"] = metadata_path
        calls["metadata_json"] = metadata_json

    monkeypatch.setattr(main_module, "write_metadata", _fake_write_metadata)

    main_module.write_resource_jsonld_metadata(_DummyMetadataObject(), include_manifest=False)

    assert "manifest_called" not in calls
    assert "completed" not in calls
    assert calls["metadata_path"] == "test-bucket/resource/.hsjsonld/dataset_metadata.json"
    assert calls["metadata_json"]["associatedMedia"] == [{
        "type": "MediaObject",
        "name": "file_manifest.json",
        "contentUrl": "https://s3.example.org/test-bucket/resource/.hsjsonld/file_manifest.json",
        "encodingFormat": "application/json",
        "contentSize": "0.0 KB",
    }]


def test_resource_metadata_status_helpers(monkeypatch):
    stored = {}

    def _fake_load_metadata(path):
        return stored.get(path, {})

    def _fake_write_metadata(path, payload):
        stored[path] = json.loads(json.dumps(payload))

    monkeypatch.setattr(s3_utils, "load_metadata", _fake_load_metadata)
    monkeypatch.setattr(s3_utils, "write_metadata", _fake_write_metadata)

    status_path = "test-bucket/resource/.hsjsonld/resource_metadata_status.json"

    default_status = s3_utils.load_resource_metadata_status(status_path)
    assert default_status == {
        "file_manifest": {
            "isDirty": False,
            "isRebuilding": False,
            "generation": 0,
            "lastRequestedAt": None,
            "lastRebuiltAt": None,
            "lockExpiresAt": None,
            "lastError": None,
        }
    }

    dirty_status = s3_utils.mark_manifest_dirty(status_path)
    assert dirty_status["file_manifest"]["isDirty"] is True
    assert dirty_status["file_manifest"]["generation"] == 1

    claimed_status, claimed = s3_utils.begin_manifest_rebuild(status_path, now=100.0, lock_ttl_seconds=10)
    assert claimed is True
    assert claimed_status["file_manifest"]["isRebuilding"] is True
    assert claimed_status["file_manifest"]["lockExpiresAt"] == 110.0

    _, claimed_again = s3_utils.begin_manifest_rebuild(status_path, now=105.0, lock_ttl_seconds=10)
    assert claimed_again is False

    failed_status = s3_utils.fail_manifest_rebuild(status_path, "boom", now=111.0)
    assert failed_status["file_manifest"]["isDirty"] is True
    assert failed_status["file_manifest"]["isRebuilding"] is False
    assert failed_status["file_manifest"]["lastError"] == "boom"

    recovered_status, claimed_after_expiry = s3_utils.begin_manifest_rebuild(status_path, now=120.0, lock_ttl_seconds=5)
    assert claimed_after_expiry is True
    assert recovered_status["file_manifest"]["lockExpiresAt"] == 125.0

    completed_status = s3_utils.complete_manifest_rebuild(status_path, now=130.0)
    assert completed_status["file_manifest"]["isDirty"] is False
    assert completed_status["file_manifest"]["isRebuilding"] is False
    assert completed_status["file_manifest"]["lastRebuiltAt"] == 130.0


def test_iter_resource_associated_media_returns_fresh_iterator(monkeypatch):
    call_count = {"count": 0}

    def _fake_iter_file_manifest(resource_root_path, enabled=False):
        assert resource_root_path == "test-bucket/resource/data/contents"
        assert enabled is True
        call_count["count"] += 1
        yield {"name": "a.txt", "contentUrl": "https://s3.example.org/test-bucket/resource/data/contents/a.txt"}

    monkeypatch.setattr("hsextract.content_types.models.iter_file_manifest", _fake_iter_file_manifest)

    metadata_object = BaseMetadataObject("test-bucket/resource/data/contents/a.txt", True)

    first_pass = list(metadata_object.iter_resource_associated_media())
    second_pass = list(metadata_object.iter_resource_associated_media())

    assert first_pass == second_pass
    assert call_count["count"] == 2


def test_raster_associated_media_reuses_filtered_cache(monkeypatch):
    iteration_count = {"count": 0}
    media_objects = [
        {
            "name": "logan.vrt",
            "contentUrl": "https://s3.example.org/test-bucket/resource/data/contents/raster_aggregation/logan.vrt",
        },
        {
            "name": "logan1.tif",
            "contentUrl": "https://s3.example.org/test-bucket/resource/data/contents/raster_aggregation/logan1.tif",
        },
        {
            "name": "logan2.tif",
            "contentUrl": "https://s3.example.org/test-bucket/resource/data/contents/raster_aggregation/logan2.tif",
        },
        {
            "name": "other.txt",
            "contentUrl": "https://s3.example.org/test-bucket/resource/data/contents/raster_aggregation/other.txt",
        },
    ]

    class _DummyMetadata:
        def __init__(self, file_path):
            self.file_path = file_path

        def model_dump(self, exclude_none=True):
            return {"file_path": self.file_path}

    def _fake_iter_resource_associated_media(self):
        iteration_count["count"] += 1
        return iter(media_objects)

    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")
    monkeypatch.setattr(RasterMetadataObject, "iter_resource_associated_media", _fake_iter_resource_associated_media)
    monkeypatch.setattr("hsextract.content_types.raster.models.list_tif_files_s3", lambda path: ["logan1.tif", "logan2.tif"])
    monkeypatch.setattr("hsextract.content_types.raster.models.encode_raster_metadata", lambda path: _DummyMetadata(path))

    metadata_object = RasterMetadataObject(
        "test-bucket/resource/data/contents/raster_aggregation/logan1.tif",
        True,
    )

    first_media = metadata_object.content_type_associated_media()
    extracted_metadata = metadata_object.extract_metadata()
    cleanup_files = metadata_object.clean_up_extracted_metadata()
    second_media = metadata_object.content_type_associated_media()

    assert [media_object["name"] for media_object in first_media] == ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert second_media == first_media
    assert extracted_metadata == {"file_path": "test-bucket/resource/data/contents/raster_aggregation/logan.vrt"}
    assert cleanup_files == [
        "test-bucket/resource/.hsjsonld/raster_aggregation/logan1.tif.json",
        "test-bucket/resource/.hsmetadata/raster_aggregation/logan1.tif.json",
        "test-bucket/resource/.hsjsonld/raster_aggregation/logan2.tif.json",
        "test-bucket/resource/.hsmetadata/raster_aggregation/logan2.tif.json",
    ]
    assert iteration_count["count"] == 2