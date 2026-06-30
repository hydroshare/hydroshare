"""
Integration test fixtures for hs_s3_proxy.

Environment variables
---------------------
HS_API_ENDPOINT     HydroShare base URL          (default: http://localhost)
HS_USERNAME         HydroShare username           (default: asdf)
HS_PASSWORD         HydroShare password           (default: asdf)
S3_PROXY_ENDPOINT   S3 proxy base URL             (default: http://localhost:9002)
S3_TEST_BUCKET      Bucket name                   (default: resource)

The fixtures automatically:
  1. Create an S3 service account via POST /hsapi/user/service/accounts/s3/
  2. Create a temporary CompositeResource via POST /hsapi/resource/
  3. Tear both down after the test session completes.

Two S3 client variants are provided:
  s3_client            – boto3 with SigV4 service-account credentials
  session_s3_client    – raw requests with Django csrftoken + sessionid cookies
"""
import io
import os
import uuid
import xml.etree.ElementTree as ET

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


# ---------------------------------------------------------------------------
# Session-cookie auth – login and raw HTTP S3 client
# ---------------------------------------------------------------------------

_S3_NS = "http://s3.amazonaws.com/doc/2006-03-01/"


class RawSessionS3Client:
    """Thin S3-compatible client that forwards Django session cookies to the
    proxy instead of signing requests with SigV4.  The interface mirrors the
    boto3 S3 client methods used in the test suite."""

    def __init__(self, session: requests.Session, endpoint: str, bucket: str):
        self._session = session
        self._endpoint = endpoint.rstrip("/")
        self._default_bucket = bucket

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _url(self, bucket: str, key: str = "") -> str:
        if key:
            return f"{self._endpoint}/{bucket}/{key}"
        return f"{self._endpoint}/{bucket}"

    @staticmethod
    def _meta(resp: requests.Response) -> dict:
        return {"ResponseMetadata": {"HTTPStatusCode": resp.status_code}}

    @staticmethod
    def _xml_find(text: str, tag: str) -> str | None:
        """Return the text of the first matching tag, namespace-aware."""
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return None
        el = root.find(f".//{{{_S3_NS}}}{tag}")
        if el is None:
            el = root.find(f".//{tag}")
        return el.text if el is not None else None

    @staticmethod
    def _xml_findall(text: str, parent_tag: str, child_tag: str) -> list[str]:
        """Return text of all *child_tag* elements inside each *parent_tag*."""
        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return []
        parents = root.findall(f".//{{{_S3_NS}}}{parent_tag}")
        if not parents:
            parents = root.findall(f".//{parent_tag}")
        results = []
        for parent in parents:
            el = parent.find(f"{{{_S3_NS}}}{child_tag}")
            if el is None:
                el = parent.find(child_tag)
            if el is not None and el.text:
                results.append(el.text)
        return results

    # ------------------------------------------------------------------
    # S3 operations
    # ------------------------------------------------------------------

    def list_objects_v2(self, Bucket: str, Prefix: str = "") -> dict:
        params: dict = {"list-type": "2"}
        if Prefix:
            params["prefix"] = Prefix
        resp = self._session.get(self._url(Bucket), params=params)
        resp.raise_for_status()
        keys = self._xml_findall(resp.text, "Contents", "Key")
        return {**self._meta(resp), "Contents": [{"Key": k} for k in keys]}

    def put_object(self, Bucket: str, Key: str, Body: bytes,
                   ContentType: str = "application/octet-stream") -> dict:
        resp = self._session.put(
            self._url(Bucket, Key),
            data=Body,
            headers={"Content-Type": ContentType},
        )
        resp.raise_for_status()
        return self._meta(resp)

    def get_object(self, Bucket: str, Key: str) -> dict:
        resp = self._session.get(self._url(Bucket, Key))
        resp.raise_for_status()
        return {
            **self._meta(resp),
            "Body": io.BytesIO(resp.content),
            "ContentType": resp.headers.get("content-type", ""),
        }

    def delete_object(self, Bucket: str, Key: str) -> dict:
        resp = self._session.delete(self._url(Bucket, Key))
        resp.raise_for_status()
        return self._meta(resp)

    def create_multipart_upload(self, Bucket: str, Key: str,
                                ContentType: str = "application/octet-stream") -> dict:
        resp = self._session.post(
            self._url(Bucket, Key),
            params={"uploads": ""},
            headers={"Content-Type": ContentType},
        )
        resp.raise_for_status()
        upload_id = self._xml_find(resp.text, "UploadId")
        return {**self._meta(resp), "UploadId": upload_id}

    def upload_part(self, Bucket: str, Key: str, UploadId: str,
                    PartNumber: int, Body: bytes) -> dict:
        resp = self._session.put(
            self._url(Bucket, Key),
            params={"partNumber": str(PartNumber), "uploadId": UploadId},
            data=Body,
        )
        resp.raise_for_status()
        return {**self._meta(resp), "ETag": resp.headers.get("ETag", "")}

    def complete_multipart_upload(self, Bucket: str, Key: str,
                                  UploadId: str, MultipartUpload: dict) -> dict:
        parts_xml = "".join(
            f"<Part>"
            f"<PartNumber>{p['PartNumber']}</PartNumber>"
            f"<ETag>{p['ETag']}</ETag>"
            f"</Part>"
            for p in MultipartUpload["Parts"]
        )
        body = (
            f"<CompleteMultipartUpload>{parts_xml}</CompleteMultipartUpload>"
        ).encode()
        resp = self._session.post(
            self._url(Bucket, Key),
            params={"uploadId": UploadId},
            data=body,
            headers={"Content-Type": "application/xml"},
        )
        resp.raise_for_status()
        return self._meta(resp)

    def abort_multipart_upload(self, Bucket: str, Key: str, UploadId: str) -> dict:
        resp = self._session.delete(
            self._url(Bucket, Key),
            params={"uploadId": UploadId},
        )
        resp.raise_for_status()
        return self._meta(resp)


@pytest.fixture(scope="session")
def session_cookies(hs_api_endpoint, hs_credentials):
    """Log in via the Django form and return a requests.Session carrying
    csrftoken + sessionid cookies."""
    username, password = hs_credentials
    login_url = f"{hs_api_endpoint}/accounts/login/"

    session = requests.Session()
    # GET the login page to receive the initial csrftoken cookie.
    _ = session.get(login_url, timeout=10, allow_redirects=True)
    csrf = session.cookies.get("csrftoken", "")

    post_resp = session.post(
        login_url,
        data={
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": csrf,
        },
        headers={"Referer": login_url},
        timeout=10,
        allow_redirects=True,
    )
    # A successful Django login redirects (302) to another page.
    assert "sessionid" in session.cookies, (
        f"Login did not set a sessionid cookie "
        f"(status={post_resp.status_code}). "
        "Check HS_USERNAME / HS_PASSWORD."
    )
    return session


@pytest.fixture(scope="session")
def session_s3_client(proxy_endpoint, test_bucket, session_cookies):
    """RawSessionS3Client authenticated with Django session cookies."""
    return RawSessionS3Client(session_cookies, proxy_endpoint, test_bucket)
