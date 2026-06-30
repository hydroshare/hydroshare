"""
Integration test fixtures for hs_s3_proxy.

Environment variables
---------------------
HS_API_ENDPOINT     HydroShare base URL          (default: http://localhost)
HS_USERNAME         HydroShare username           (required)
HS_PASSWORD         HydroShare password           (required)
S3_PROXY_ENDPOINT   S3 proxy base URL             (default: http://localhost:9002)
S3_TEST_BUCKET      Bucket name                   (default: resource)

The fixtures automatically:
  1. Create an S3 service account via POST /hsapi/user/service/accounts/s3/
  2. Create a temporary CompositeResource via POST /hsapi/resource/
  3. Tear both down after the test session completes.
"""
import os
import uuid

import boto3
import pytest
import requests
from botocore.config import Config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.skip(
            f"Environment variable {name!r} is not set – "
            "skipping proxy integration tests."
        )
    return value


# ---------------------------------------------------------------------------
# Session-scoped fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def hs_api_endpoint() -> str:
    return os.environ.get("HS_API_ENDPOINT", "http://localhost")


@pytest.fixture(scope="session")
def hs_credentials():
    username = os.environ.get("HS_USERNAME", "asdf")
    password = os.environ.get("HS_PASSWORD", "asdf")
    return username, password


@pytest.fixture(scope="session")
def hs_session(hs_api_endpoint, hs_credentials):
    """Authenticated requests.Session against the HydroShare API."""
    username, password = hs_credentials
    session = requests.Session()
    session.auth = (username, password)
    # Fetch a CSRF token so that POST requests are accepted by Django.
    resp = session.get(f"{hs_api_endpoint}/hsapi/userInfo/", timeout=10)
    resp.raise_for_status()
    csrf = session.cookies.get("csrftoken")
    if csrf:
        session.headers["X-CSRFToken"] = csrf
    return session


@pytest.fixture(scope="session")
def proxy_endpoint() -> str:
    return os.environ.get("S3_PROXY_ENDPOINT", "http://localhost:9002")


@pytest.fixture(scope="session")
def test_bucket() -> str:
    return os.environ.get("S3_TEST_BUCKET", "resource")


@pytest.fixture(scope="session")
def service_account(hs_api_endpoint, hs_session):
    """
    Create an S3 service account for the authenticated user and delete it
    after the session.  Returns (access_key, secret_key).
    """
    url = f"{hs_api_endpoint}/hsapi/user/service/accounts/s3/"
    resp = hs_session.post(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    access_key = data["access_key"]
    secret_key = data["secret_key"]

    yield access_key, secret_key

    # Teardown – delete the service account.
    delete_url = f"{hs_api_endpoint}/hsapi/user/service/accounts/s3/{access_key}"
    try:
        hs_session.delete(delete_url, timeout=10)
    except Exception as exc:
        print(f"Warning: failed to delete service account {access_key}: {exc}")


@pytest.fixture(scope="session")
def test_resource_id(hs_api_endpoint, hs_session):
    """
    Create a throw-away CompositeResource and delete it after the session.
    Returns the resource short ID string.
    """
    url = f"{hs_api_endpoint}/hsapi/resource/"
    resp = hs_session.post(
        url,
        data={
            "resource_type": "CompositeResource",
            "title": f"hs_s3_proxy integration test {uuid.uuid4().hex}",
        },
        timeout=30,
    )
    resp.raise_for_status()
    resource_id = resp.json()["resource_id"]

    yield resource_id

    # Teardown – delete the resource.
    delete_url = f"{hs_api_endpoint}/hsapi/resource/{resource_id}/"
    try:
        hs_session.delete(delete_url, timeout=30)
    except Exception as exc:
        print(f"Warning: failed to delete resource {resource_id}: {exc}")


@pytest.fixture(scope="session")
def s3_client(proxy_endpoint, service_account):
    """Boto3 S3 client pointed at the hs_s3_proxy, signed with the auto-created service account."""
    access_key, secret_key = service_account
    client = boto3.client(
        "s3",
        endpoint_url=proxy_endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            # Only attach checksums when the operation actually requires them
            # (avoids SignatureDoesNotMatch on UploadPart against MinIO/GCS).
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )
    return client


# ---------------------------------------------------------------------------
# Per-test fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def unique_prefix(test_resource_id) -> str:
    """Returns a unique object key prefix scoped to the test resource."""
    run_id = uuid.uuid4().hex
    return f"{test_resource_id}/data/contents/test-{run_id}"
