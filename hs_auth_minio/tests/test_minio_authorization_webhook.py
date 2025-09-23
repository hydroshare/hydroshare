import pytest
from fastapi.testclient import TestClient
from redis import Redis

from api.routers.minio import router as minio_router

client = TestClient(minio_router)

# 7 users, 2 groups, and 4 resources are defined in the init-scripts/hydroshare-staged-snapshot.sql file.
# The following tests loop through all 4 resources and check the authorization for each user and group.
# The users, groups and resources are defined as follows:

# user1 (18) owns the resource
# user2 (19) does not have access to the resource
# user3 (20) has view access to the resource
# user4 (22) has edit access to the resource
# user5 (23) is an owner
# user6 (24) is is a member of view group
# user7 (25) is a member of edit group


# view group has view access to f211b93642f84c55a0bdd1b12880e32e with user6 as a member
# edit group has edit access to f211b93642f84c55a0bdd1b12880e32e with user7 as a member

# f211b93642f84c55a0bdd1b12880e32e is the resource id for the private resource
# d5c432ae01eb4f03a73d589e54d341b3 is the resource id for the private link resource
# a2c0df5bf3eb4d8c8a34beaffe169f91 is the resource id for the public resource
# 5670903e39d54026a729abd4cc148f99 is the resource id for the discoverable resource


@pytest.fixture(autouse=True)
def clear_redis_cache():
    redis_client = Redis(host='redis', port=6379, db=0)
    redis_client.flushdb()


# private resource checks
def check_private_view_authorization(request_body, resource_id=None):
    if resource_id:
        request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is the owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


def check_private_edit_authorization(request_body, resource_id=None):
    if resource_id:
        request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is the owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


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
def test_private_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_view_authorization(request_body)


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
def test_private_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_edit_authorization(request_body)


# private link actions
def check_private_link_view_authorization(request_body, resource_id="d5c432ae01eb4f03a73d589e54d341b3"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


def check_private_link_edit_authorization(request_body, resource_id="d5c432ae01eb4f03a73d589e54d341b3"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_get_object_legal_hold.json",
        "user1_get_object_retention.json",
        "user1_list_bucket.json",
        "user1_list_objects_v2.json",
    ],
)
def test_private_link_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_link_view_authorization(request_body)


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
def test_private_link_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_private_link_edit_authorization(request_body)


# public actions
def check_public_view_authorization(request_body, resource_id="a2c0df5bf3eb4d8c8a34beaffe169f91"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


def check_public_edit_authorization(request_body, resource_id="a2c0df5bf3eb4d8c8a34beaffe169f91"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_get_object_legal_hold.json",
        "user1_get_object_retention.json",
        "user1_list_bucket.json",
        "user1_list_objects_v2.json",
    ],
)
def test_public_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_public_view_authorization(request_body)


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
def test_public_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_public_edit_authorization(request_body)


# discoverable actions
def check_discoverable_view_get_authorization(request_body, resource_id="5670903e39d54026a729abd4cc148f99"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


# discoverable actions
def check_discoverable_view_authorization(request_body, resource_id="5670903e39d54026a729abd4cc148f99"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


def check_discoverable_edit_authorization(request_body, resource_id="5670903e39d54026a729abd4cc148f99"):
    request_body = request_body.replace("f211b93642f84c55a0bdd1b12880e32e", resource_id)
    # user1 is owner and quota holder
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user2 has no explicit access
    request_body = request_body.replace("user1", "user2")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user3 has view access
    request_body = request_body.replace("user2", "user3")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user4 has edit access
    request_body = request_body.replace("user3", "user4")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user5 is an owner
    request_body = request_body.replace("user4", "user5")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # user6 is a member of view group
    request_body = request_body.replace("user5", "user6")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}

    # user7 is a member of edit group
    request_body = request_body.replace("user6", "user7")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}


@pytest.mark.parametrize(
    "action_json",
    [
        "user1_get_object_legal_hold.json",
        "user1_get_object_retention.json",
    ],
)
def test_discoverable_view_get(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_view_get_authorization(request_body)


@pytest.mark.parametrize(
    "action_json", ["user1_list_bucket.json", "user1_list_objects.json", "user1_list_objects_v2.json"]
)
def test_discoverable_view(action_json):
    with open(f"tests/json_payloads/view_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_view_authorization(request_body)


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
def test_discoverable_edit(action_json):
    with open(f"tests/json_payloads/edit_authorization/{action_json}", "r") as file:
        request_body = file.read()
    check_discoverable_edit_authorization(request_body)


# admin actions
def test_admin_request():
    with open("tests/json_payloads/minio_admin_request.json", "r") as file:
        request_body = file.read()
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # assert cuahsi has authorization
    request_body = request_body.replace("minioadmin", "cuahsi")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": True}}

    # assert user1 does not have authorization
    request_body = request_body.replace("cuahsi", "user1")
    response = client.post("/authorization/", data=request_body)
    assert response.status_code == 200
    assert response.json() == {"result": {"allow": False}}
