import pytest
from fastapi.testclient import TestClient
from redis import Redis

from api.routers.access_control_changed import router as access_control_changed_router
from api.routers.minio import router as minio_router

minio_client = TestClient(minio_router)
access_control_changed_client = TestClient(access_control_changed_router)


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
def test_view_user_access_change_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = minio_client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # update user2 to have view access
    with open("tests/json_payloads/access_control_changed/user_access/to_view.json", "r") as file:
        access_control_changed_payload = file.read()
    response = access_control_changed_client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # user2 has view access
    request_body = request_body.replace("user1", "user2")
    response = minio_client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


@pytest.mark.parametrize(
    "action_json",
    [
        "view_authorization/user1_get_object_legal_hold.json",
        "view_authorization/user1_get_object_retention.json",
        "view_authorization/user1_list_bucket.json",
        "view_authorization/user1_list_objects.json",
        "/view_authorization/user1_list_objects_v2.json",
        "edit_authorization/user1_put_object.json",
        "edit_authorization/user1_put_object_legal_hold.json",
        "edit_authorization/user1_upload_part.json",
        "edit_authorization/user1_delete_object.json",
        "edit_authorization/user1_delete_objects.json",
    ],
)
def test_edit_user_access_change_edit(action_json):
    with open(f"tests/json_payloads/{action_json}", "r") as file:
        request_body = file.read()

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = minio_client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # update user2 to have edit access
    with open("tests/json_payloads/access_control_changed/user_access/to_edit.json", "r") as file:
        access_control_changed_payload = file.read()
    response = access_control_changed_client.post("/hook/", data=access_control_changed_payload)
    assert response.status_code == 204

    # user2 has edit access
    request_body = request_body.replace("user1", "user2")
    response = minio_client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}
