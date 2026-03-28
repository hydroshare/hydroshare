import time
import pytest

from hsextract import main as main_module
from hsextract.content_types.models import JsonldMetadataObject
from hsextract.event_batch_processing import ManifestRebuildCoordinator, ManifestRebuildRequest


@pytest.fixture(autouse=True)
def _reset_manifest_coordinator_singleton():
    ManifestRebuildCoordinator.reset_instance_for_testing()
    yield
    ManifestRebuildCoordinator.reset_instance_for_testing()


def test_manifest_rebuild_coordinator_coalesces_duplicate_requests():
    completed_requests = []

    def _rebuild_callback(request):
        completed_requests.append(request)

    coordinator = ManifestRebuildCoordinator(
        rebuild_callback=_rebuild_callback,
        debounce_delay_seconds=0.05,
        max_wait_seconds=0.2,
    )
    request = ManifestRebuildRequest(
        resource_id="resource-id",
        resource_contents_path="test-bucket/resource/data/contents",
        manifest_path="test-bucket/resource/.hsjsonld/file_manifest.json",
        status_path="test-bucket/resource/.hsjsonld/resource_metadata_status.json",
        metadata_path="test-bucket/resource/.hsjsonld/dataset_metadata.json",
    )

    coordinator.enqueue(request)
    coordinator.enqueue(request)
    time.sleep(0.12)
    coordinator.stop()

    assert len(completed_requests) == 1
    assert completed_requests[0].resource_id == "resource-id"


def test_manifest_rebuild_coordinator_releases_request_at_max_wait():
    coordinator = ManifestRebuildCoordinator(
        rebuild_callback=lambda request: None,
        debounce_delay_seconds=1.0,
        max_wait_seconds=0.15,
    )
    request = ManifestRebuildRequest(
        resource_id="resource-id",
        resource_contents_path="test-bucket/resource/data/contents",
        manifest_path="test-bucket/resource/.hsjsonld/file_manifest.json",
        status_path="test-bucket/resource/.hsjsonld/resource_metadata_status.json",
        metadata_path="test-bucket/resource/.hsjsonld/dataset_metadata.json",
    )

    coordinator._merge_request(request, 0.00)
    coordinator._merge_request(request, 0.05)
    coordinator._merge_request(request, 0.10)

    assert coordinator._pop_ready_requests(0.14) == []
    ready_requests = coordinator._pop_ready_requests(0.16)

    assert ready_requests == [request]


def test_enqueue_manifest_rebuild_claims_and_queues_once(monkeypatch):
    calls = {}

    class _DummyCoordinator:
        def enqueue(self, request):
            calls["request"] = request

    monkeypatch.setattr(main_module, "begin_manifest_rebuild", lambda path: ({}, True))
    monkeypatch.setattr(ManifestRebuildCoordinator, "get_instance", lambda rebuild_callback: _DummyCoordinator())

    md = JsonldMetadataObject("test-bucket", "resource")

    claimed = main_module.enqueue_manifest_rebuild(md)

    assert claimed is True
    assert calls["request"].resource_id == "resource"
    assert calls["request"].status_path == "test-bucket/resource/.hsjsonld/resource_metadata_status.json"


def test_enqueue_manifest_rebuild_does_not_queue_without_claim(monkeypatch):
    calls = {"enqueue_count": 0}

    class _DummyCoordinator:
        def enqueue(self, request):
            del request
            calls["enqueue_count"] += 1

    monkeypatch.setattr(main_module, "begin_manifest_rebuild", lambda path: ({}, False))
    monkeypatch.setattr(ManifestRebuildCoordinator, "get_instance", lambda rebuild_callback: _DummyCoordinator())

    md = JsonldMetadataObject("test-bucket", "resource")

    claimed = main_module.enqueue_manifest_rebuild(md)

    assert claimed is False
    assert calls["enqueue_count"] == 0


def test_rebuild_file_manifest_for_resource_updates_associated_media_and_completes(monkeypatch):
    calls = {}
    request = ManifestRebuildRequest(
        resource_id="resource-id",
        resource_contents_path="test-bucket/resource/data/contents",
        manifest_path="test-bucket/resource/.hsjsonld/file_manifest.json",
        status_path="test-bucket/resource/.hsjsonld/resource_metadata_status.json",
        metadata_path="test-bucket/resource/.hsjsonld/dataset_metadata.json",
    )

    monkeypatch.setenv("AWS_S3_ENDPOINT_URL", "https://s3.example.org")

    def _fake_write_file_manifest(resource_contents_path, manifest_path, enabled=False):
        calls["manifest"] = {
            "resource_contents_path": resource_contents_path,
            "manifest_path": manifest_path,
            "enabled": enabled,
        }
        return {"name": "ignored-by-rebuild"}

    def _fake_load_metadata(path):
        assert path == request.metadata_path
        return {"associatedMedia": [{"name": "stale.json", "contentUrl": "https://stale.example.org/file.json"}]}

    def _fake_write_metadata(path, payload):
        calls["metadata"] = {"path": path, "payload": payload}

    monkeypatch.setattr(main_module, "write_file_manifest", _fake_write_file_manifest)
    monkeypatch.setattr(main_module, "load_metadata", _fake_load_metadata)
    monkeypatch.setattr(main_module, "write_metadata", _fake_write_metadata)
    monkeypatch.setattr(main_module, "complete_manifest_rebuild", lambda path: calls.setdefault("completed", path))
    monkeypatch.setattr(main_module, "fail_manifest_rebuild", lambda path, error: calls.setdefault("failed", (path, error)))

    main_module.rebuild_file_manifest_for_resource(request)

    assert calls["manifest"] == {
        "resource_contents_path": "test-bucket/resource/data/contents",
        "manifest_path": "test-bucket/resource/.hsjsonld/file_manifest.json",
        "enabled": True,
    }
    assert calls["metadata"]["path"] == request.metadata_path
    assert calls["metadata"]["payload"]["associatedMedia"] == [{
        "type": "MediaObject",
        "name": "file_manifest.json",
        "contentUrl": "https://s3.example.org/test-bucket/resource/.hsjsonld/file_manifest.json",
        "encodingFormat": "application/json",
        "contentSize": "0.0 KB",
    }]
    assert calls["completed"] == request.status_path
    assert "failed" not in calls


def test_rebuild_file_manifest_for_resource_records_failure(monkeypatch):
    calls = {}
    request = ManifestRebuildRequest(
        resource_id="resource-id",
        resource_contents_path="test-bucket/resource/data/contents",
        manifest_path="test-bucket/resource/.hsjsonld/file_manifest.json",
        status_path="test-bucket/resource/.hsjsonld/resource_metadata_status.json",
        metadata_path="test-bucket/resource/.hsjsonld/dataset_metadata.json",
    )

    monkeypatch.setattr(main_module, "write_file_manifest", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(main_module, "fail_manifest_rebuild", lambda path, error: calls.setdefault("failed", (path, error)))
    monkeypatch.setattr(main_module, "complete_manifest_rebuild", lambda path: calls.setdefault("completed", path))

    main_module.rebuild_file_manifest_for_resource(request)

    assert calls["failed"] == (request.status_path, "boom")
    assert "completed" not in calls


def test_handle_resource_jsonld_event_enqueues_only_manifest_get_requests(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "enqueue_manifest_rebuild",
        lambda md: calls.append(
            {
                "resource_id": md.resource_id,
                "bucket_name": md.bucket_name,
            }
        ),
    )

    main_module.handle_resource_jsonld_event(
        key="test-bucket/resource/.hsjsonld/file_manifest.json",
        bucket="test-bucket",
        resource_id="resource",
        event_name="s3:ObjectAccessed:Get",
        file_updated=False,
    )
    main_module.handle_resource_jsonld_event(
        key="test-bucket/resource/.hsjsonld/other.json",
        bucket="test-bucket",
        resource_id="resource",
        event_name="s3:ObjectAccessed:Get",
        file_updated=False,
    )
    main_module.handle_resource_jsonld_event(
        key="test-bucket/resource/.hsjsonld/file_manifest.json",
        bucket="test-bucket",
        resource_id="resource",
        event_name="s3:ObjectCreated:Put",
        file_updated=True,
    )

    assert calls == [{
        "resource_id": "resource",
        "bucket_name": "test-bucket",
    }]


def test_handle_root_metadata_event_skips_manifest_rebuild(monkeypatch):
    calls = []

    def _fake_write_resource_jsonld_metadata(md, include_manifest=True):
        calls.append({
            "resource_id": md.resource_id,
            "include_manifest": include_manifest,
            "file_object_path": md.file_object_path,
        })

    monkeypatch.setattr(main_module, "write_resource_jsonld_metadata", _fake_write_resource_jsonld_metadata)

    for metadata_file in ("user_metadata.json", "system_metadata.json"):
        main_module.handle_root_resource_metadata_event(
            key=f"test-bucket/resource/.hsmetadata/{metadata_file}",
            bucket="test-bucket",
            resource_id="resource",
            file_updated=True,
        )

    assert calls == [
        {
            "resource_id": "resource",
            "include_manifest": False,
            "file_object_path": "test-bucket/resource/.hsmetadata/user_metadata.json",
        },
        {
            "resource_id": "resource",
            "include_manifest": False,
            "file_object_path": "test-bucket/resource/.hsmetadata/system_metadata.json",
        },
    ]


def test_manifest_rebuild_singleton_rejects_callback_mismatch():
    callback_a = lambda request: None
    callback_b = lambda request: None

    first = ManifestRebuildCoordinator.get_instance(callback_a)
    assert first is not None

    with pytest.raises(ValueError, match="different rebuild_callback"):
        ManifestRebuildCoordinator.get_instance(callback_b)


def test_manifest_rebuild_singleton_restart_after_stop(monkeypatch):
    completed_requests = []
    monkeypatch.setenv("HS_EXTRACT_MANIFEST_DEBOUNCE_DELAY_SECONDS", "0.05")
    monkeypatch.setenv("HS_EXTRACT_MANIFEST_MAX_WAIT_SECONDS", "0.1")

    def _rebuild_callback(request):
        completed_requests.append(request)

    coordinator = ManifestRebuildCoordinator.get_instance(_rebuild_callback)
    request = ManifestRebuildRequest(
        resource_id="resource-id",
        resource_contents_path="test-bucket/resource/data/contents",
        manifest_path="test-bucket/resource/.hsjsonld/file_manifest.json",
        status_path="test-bucket/resource/.hsjsonld/resource_metadata_status.json",
        metadata_path="test-bucket/resource/.hsjsonld/dataset_metadata.json",
    )

    coordinator.enqueue(request)
    time.sleep(0.2)
    coordinator.stop()

    coordinator.enqueue(request)
    time.sleep(0.2)
    coordinator.stop()

    assert len(completed_requests) >= 2
