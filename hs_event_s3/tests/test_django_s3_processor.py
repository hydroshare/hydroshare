import importlib
import sys

import pytest
from django.contrib.auth.models import User
from fastapi.testclient import TestClient

from hs_core import hydroshare


@pytest.fixture
def event_admin(db):
    user, _ = User.objects.get_or_create(
        username="event-admin",
        defaults={
            "email": "event-admin@example.com",
            "first_name": "Event",
            "last_name": "Admin",
            "is_superuser": True,
            "is_staff": True,
        },
    )
    if not user.is_superuser or not user.is_staff:
        user.is_superuser = True
        user.is_staff = True
        user.save(update_fields=["is_superuser", "is_staff"])
    return user


@pytest.fixture
def event_app(event_admin):
    sys.modules.pop("hs_event_s3.hsevent.processors.hs_django_s3_processor", None)
    module = importlib.import_module("hs_event_s3.hsevent.processors.hs_django_s3_processor")
    return importlib.reload(module)


@pytest.fixture
def client(event_app):
    return TestClient(event_app.app)


@pytest.mark.django_db
def test_healthz(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_unsupported_event_type_is_ignored(client):
    response = client.post(
        "/",
        headers={"ce-type": "google.cloud.storage.object.v1.archived"},
        json={"name": "abc123/data/contents/file.txt"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "unsupported event type"}


@pytest.mark.django_db
def test_invalid_json_returns_400(client):
    response = client.post(
        "/",
        headers={"ce-type": "google.cloud.storage.object.v1.finalized"},
        content="not-json",
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid JSON payload"}


@pytest.mark.django_db
def test_missing_name_returns_400(client):
    response = client.post(
        "/",
        headers={"ce-type": "google.cloud.storage.object.v1.finalized"},
        json={},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Missing 'name' in event data"}


@pytest.mark.django_db
def test_non_contents_path_is_ignored(client):
    response = client.post(
        "/",
        headers={"ce-type": "google.cloud.storage.object.v1.finalized"},
        json={"name": "abc123/system-metadata.json"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ignored", "reason": "not in contents directory"}


@pytest.mark.django_db
def test_deleted_event_removes_resource_file(client, composite_resource, tmp_path):
    resource, _ = composite_resource
    file_path = tmp_path / "event-file.txt"
    file_path.write_text("event file contents")

    with file_path.open("rb") as file_handle:
        hydroshare.add_resource_files(resource.short_id, file_handle)

    resource.refresh_from_db()
    assert resource.files.filter(resource_file__endswith="event-file.txt").exists()

    response = client.post(
        "/",
        headers={"ce-type": "google.cloud.storage.object.v1.deleted"},
        json={"name": f"{resource.short_id}/data/contents/event-file.txt"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "resource_id": resource.short_id}

    resource.refresh_from_db()
    assert not resource.files.filter(resource_file__endswith="event-file.txt").exists()
