import pytest
from fastapi.testclient import TestClient
from redis import Redis

from api.routers.access_control_changed import router as access_control_changed_router
from tests.test_minio_authorization_webhook import (
    check_discoverable_edit_authorization,
    check_discoverable_view_authorization,
    check_discoverable_view_get_authorization,
    check_private_edit_authorization,
    check_private_link_edit_authorization,
    check_private_link_view_authorization,
    check_private_view_authorization,
    check_public_edit_authorization,
    check_public_view_authorization,
)

client = TestClient(access_control_changed_router)


@pytest.fixture(autouse=True)
def clear_redis_cache():
    redis_client = Redis(host='redis', port=6379, db=0)
    redis_client.flushdb()


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_get_object_legal_hold.json",
        "user1_get_object_retention.json",
        "user1_list_bucket.json",
        "user1_list_objects.json",
        "user1_list_objects_v2.json",
    ],
)
def test_private_to_public_view(action_json):
    # populate the cache
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)

    # update resource to public
    with open("tests/json_payloads/access_control_changed/from_private/to_public.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check public view authorization
    check_public_view_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_put_object.json",
        "user1_put_object_legal_hold.json",
        "user1_upload_part.json",
        "user1_delete_object.json",
        "user1_delete_objects.json",
    ],
)
def test_private_to_public_edit(action_json):
    # populate the cache
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_edit_authorization(request_body)

    # update resource to public
    with open("tests/json_payloads/access_control_changed/from_private/to_public.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check public edit authorization
    check_public_edit_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_get_object_legal_hold.json",
        "user1_get_object_retention.json",
        "user1_list_bucket.json",
        "user1_list_objects_v2.json",
    ],
)
def test_private_to_private_link_view(action_json):
    # populate the cache
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)

    # update resource to private link sharing
    with open("tests/json_payloads/access_control_changed/from_private/to_private_sharing.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check private link view authorization
    check_private_link_view_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_put_object.json",
        "user1_put_object_legal_hold.json",
        "user1_upload_part.json",
        "user1_delete_object.json",
        "user1_delete_objects.json",
    ],
)
def test_private_to_private_link_edit(action_json):
    # populate the cache
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_edit_authorization(request_body)

    # update resource to private link sharing
    with open("tests/json_payloads/access_control_changed/from_private/to_private_sharing.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check private link view authorization
    check_private_link_edit_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize("action_json", ["user1_list_bucket.json", "user1_list_objects_v2.json"])
def test_private_to_discoverable_view(action_json):
    # populate the cache
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)

    # update resource to discoverable sharing
    with open("tests/json_payloads/access_control_changed/from_private/to_discoverable.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check discoverable view authorization
    check_discoverable_view_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize("action_json", ["user1_get_object_legal_hold.json", "user1_get_object_retention.json"])
def test_private_to_discoverable_view_get(action_json):
    # populate the cache
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)

    # update resource to discoverable sharing
    with open("tests/json_payloads/access_control_changed/from_private/to_discoverable.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check discoverable view authorization
    check_discoverable_view_get_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_put_object.json",
        "user1_put_object_legal_hold.json",
        "user1_upload_part.json",
        "user1_delete_object.json",
        "user1_delete_objects.json",
    ],
)
def test_private_to_discoverable_edit(action_json):
    # populate the cache
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_edit_authorization(request_body)

    # update resource to discoverable sharing
    with open("tests/json_payloads/access_control_changed/from_private/to_discoverable.json", "r") as file:
        access_control_changed_payload = file.read()
    response = client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # check discoverable edit authorization
    check_discoverable_edit_authorization(request_body, "f211b93642f84c55a0bdd1b12880e32e")
