from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.events import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_celery():
    with patch("api.routers.events.celery_app") as mock_app:
        mock_app.send_task = MagicMock()
        yield mock_app


def base_event(**overrides):
    data = {
        "action": "write",
        "bucket": "hydroshare",
        "object_path": "data/contents/somefile.csv",
        "username": "user1",
        "user_id": 42,
        "file_size": 1024,
        "zone": "us-east-1",
    }
    data.update(overrides)
    return data


class TestReceiveS3Event:
    def test_returns_204_for_valid_event(self, mock_celery):
        response = client.post("/event/", json=base_event())
        assert response.status_code == 204

    def test_dispatches_process_s3_event_task(self, mock_celery):
        event = base_event()
        client.post("/event/", json=event)

        mock_celery.send_task.assert_any_call(
            "hs_event_s3.tasks.process_s3_event",
            kwargs={
                "action": event["action"],
                "bucket": event["bucket"],
                "object_path": event["object_path"],
                "username": event["username"],
                "user_id": event["user_id"],
                "zone": event["zone"],
            },
            queue="s3_events",
        )

    def test_dispatches_extract_metadata_for_data_file(self, mock_celery):
        event = base_event(object_path="data/contents/somefile.csv")
        client.post("/event/", json=event)

        mock_celery.send_task.assert_any_call(
            "hs_extract.tasks.extract_metadata",
            kwargs={
                "action": event["action"],
                "bucket": event["bucket"],
                "object_path": event["object_path"],
                "file_size": event["file_size"],
                "zone": event["zone"],
            },
            queue="extract",
        )

    def test_does_not_dispatch_extract_metadata_for_jsonld_metadata_file(self, mock_celery):
        event = base_event(object_path="abc123/.hsjsonld/dataset_metadata.json")
        client.post("/event/", json=event)

        for call in mock_celery.send_task.call_args_list:
            assert call.args[0] != "hs_extract.tasks.extract_metadata"

    def test_dispatches_sync_discovery_collection_for_jsonld_metadata_file(self, mock_celery):
        event = base_event(object_path="abc123/.hsjsonld/dataset_metadata.json")
        client.post("/event/", json=event)

        mock_celery.send_task.assert_any_call(
            "hs_event_s3.tasks.sync_discovery_collection",
            kwargs={
                "action": event["action"],
                "bucket": event["bucket"],
                "object_path": event["object_path"],
                "zone": event["zone"],
            },
            queue="s3_events",
        )

    def test_does_not_dispatch_sync_discovery_for_non_jsonld_file(self, mock_celery):
        event = base_event(object_path="data/contents/somefile.csv")
        client.post("/event/", json=event)

        for call in mock_celery.send_task.call_args_list:
            assert call.args[0] != "hs_event_s3.tasks.sync_discovery_collection"

    def test_user_id_is_optional(self, mock_celery):
        event = base_event()
        del event["user_id"]
        response = client.post("/event/", json=event)
        assert response.status_code == 204

    def test_file_size_defaults_to_zero(self, mock_celery):
        event = base_event()
        del event["file_size"]
        response = client.post("/event/", json=event)
        assert response.status_code == 204

    def test_missing_required_field_returns_422(self, mock_celery):
        event = base_event()
        del event["action"]
        response = client.post("/event/", json=event)
        assert response.status_code == 422

    def test_only_process_s3_event_dispatched_for_data_file(self, mock_celery):
        """A regular data file triggers exactly process_s3_event and extract_metadata."""
        event = base_event(object_path="data/contents/report.pdf")
        client.post("/event/", json=event)

        task_names = [call.args[0] for call in mock_celery.send_task.call_args_list]
        assert "hs_event_s3.tasks.process_s3_event" in task_names
        assert "hs_extract.tasks.extract_metadata" in task_names
        assert "hs_event_s3.tasks.sync_discovery_collection" not in task_names

    def test_jsonld_event_dispatches_process_and_sync_but_not_extract(self, mock_celery):
        event = base_event(object_path="abc123/.hsjsonld/dataset_metadata.json")
        client.post("/event/", json=event)

        task_names = [call.args[0] for call in mock_celery.send_task.call_args_list]
        assert "hs_event_s3.tasks.process_s3_event" in task_names
        assert "hs_event_s3.tasks.sync_discovery_collection" in task_names
        assert "hs_extract.tasks.extract_metadata" not in task_names
