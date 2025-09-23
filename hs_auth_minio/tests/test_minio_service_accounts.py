import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from api.routers.service_accounts import router as service_accounts_router

client = TestClient(service_accounts_router)


@pytest.fixture
def mock_service_account_data():
    return {
        "username": "testuser" + str(uuid.uuid4()),  # Generate a unique username for each test
    }


def test_create_service_account(mock_service_account_data):
    response = client.post("/auth/minio/sa/", json=mock_service_account_data)
    assert response.status_code == 201
    response_json = response.json()
    assert "access_key" in response_json
    assert "secret_key" in response_json


def test_get_service_accounts(mock_service_account_data):
    response = client.post("/auth/minio/sa/", json=mock_service_account_data)
    assert response.status_code == 201
    access_key = response.json()["access_key"]
    response = client.get(f"/auth/minio/sa/{mock_service_account_data['username']}")
    assert response.status_code == 200
    service_accounts = response.json().get("service_accounts")
    assert isinstance(service_accounts, list)
    assert len(service_accounts) == 1
    service_account = service_accounts[0]
    assert "access_key" in service_account
    assert service_account["access_key"] == access_key
    assert "expiry" in service_account
    expiry_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    assert service_account["expiry"] == f"{expiry_date} 00:00:00 +0000 UTC"


def test_delete_service_account(mock_service_account_data):
    response = client.post("/auth/minio/sa/", json=mock_service_account_data)
    assert response.status_code == 201
    access_key = response.json()["access_key"]
    response = client.get(f"/auth/minio/sa/{mock_service_account_data['username']}")
    assert response.status_code == 200
    assert len(response.json()["service_accounts"]) == 1
    response = client.delete(f"/auth/minio/sa/{access_key}")
    assert response.status_code == 204
    response = client.get(f"/auth/minio/sa/{mock_service_account_data['username']}")
    assert response.status_code == 200
    assert len(response.json()["service_accounts"]) == 0
