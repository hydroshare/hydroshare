import base64
import hashlib
import hmac
import json
import uuid
import zlib
from urllib.parse import quote

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from api.database import engine
from api.routers.minio import router


app = FastAPI()
app.include_router(router)
client = TestClient(app)


def _encode_session_data(session_dict):
    payload = json.dumps(session_dict, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(payload)
    b64 = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
    return f".{b64}:1stub:signature-not-validated"


def _build_sigv4_auth_info(method, path, headers, query_params, payload_hash, secret_key, access_key):
    signed_headers = "host;x-amz-date"
    date = "20260701"
    region = "us-east-1"
    service = "s3"

    canonical_uri = quote(path, safe="/~")
    canonical_query_string = "&".join(
        f"{quote(k, safe='~')}={quote(str(v), safe='~')}" for k, v in sorted(query_params.items())
    )
    canonical_headers = f"host:{headers['host']}\nx-amz-date:{headers['x-amz-date']}\n"
    canonical_request = "\n".join(
        [method, canonical_uri, canonical_query_string, canonical_headers, signed_headers, payload_hash]
    )

    algorithm = "AWS4-HMAC-SHA256"
    credential_scope = f"{date}/{region}/{service}/aws4_request"
    canonical_request_hash = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = "\n".join([algorithm, headers["x-amz-date"], credential_scope, canonical_request_hash])

    k_secret = ("AWS4" + secret_key).encode("utf-8")
    k_date = hmac.new(k_secret, date.encode("utf-8"), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode("utf-8"), hashlib.sha256).digest()
    k_service = hmac.new(k_region, service.encode("utf-8"), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    return {
        "access_key": access_key,
        "signature": signature,
        "signed_headers": signed_headers,
        "date": date,
        "region": region,
        "service": service,
    }


@pytest.fixture
def db_user():
    with engine.connect() as con:
        row = con.execute(
            text("SELECT id, username FROM auth_user WHERE username = 'user1' LIMIT 1")
        ).fetchone()
        if not row:
            row = con.execute(text("SELECT id, username FROM auth_user LIMIT 1")).fetchone()
    assert row is not None
    return int(row[0]), str(row[1])


@pytest.fixture
def created_rows():
    records = {"session_keys": [], "token_keys": []}
    yield records
    with engine.begin() as con:
        for session_key in records["session_keys"]:
            con.execute(
                text("DELETE FROM django_session WHERE session_key = :session_key"),
                {"session_key": session_key},
            )
        for token_key in records["token_keys"]:
            con.execute(text("DELETE FROM authtoken_token WHERE key = :token_key"), {"token_key": token_key})


def _insert_test_session(user_id, created_rows):
    session_key = uuid.uuid4().hex[:32]
    session_data = _encode_session_data({"_auth_user_id": str(user_id)})
    with engine.begin() as con:
        con.execute(
            text(
                """
                INSERT INTO django_session (session_key, session_data, expire_date)
                VALUES (:session_key, :session_data, NOW() + interval '1 day')
                """
            ),
            {"session_key": session_key, "session_data": session_data},
        )
    created_rows["session_keys"].append(session_key)
    return session_key


def _insert_test_service_token(user_id, created_rows):
    token_key = uuid.uuid4().hex
    with engine.begin() as con:
        con.execute(
            text(
                """
                INSERT INTO authtoken_token (key, created, user_id)
                VALUES (:token_key, NOW(), :user_id)
                """
            ),
            {"token_key": token_key, "user_id": user_id},
        )
    created_rows["token_keys"].append(token_key)
    return token_key


def test_verify_signature_missing_access_key():
    response = client.post(
        "/verify-signature/",
        json={
            "method": "GET",
            "path": "/hydroshare/resource",
            "headers": {},
            "query_params": {},
            "payload_hash": hashlib.sha256(b"").hexdigest(),
            "auth_info": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "missing_access_key"}


def test_verify_signature_allows_valid_database_backed_signature(db_user, created_rows):
    user_id, username = db_user
    token_key = _insert_test_service_token(user_id, created_rows)
    access_key = f"{username}:{token_key}"

    method = "GET"
    path = "/hydroshare/resource"
    headers = {"host": "localhost", "x-amz-date": "20260701T000000Z"}
    query_params = {"x-id": "GetObject"}
    payload_hash = hashlib.sha256(b"").hexdigest()
    auth_info = _build_sigv4_auth_info(
        method=method,
        path=path,
        headers=headers,
        query_params=query_params,
        payload_hash=payload_hash,
        secret_key=token_key,
        access_key=access_key,
    )

    response = client.post(
        "/verify-signature/",
        json={
            "method": method,
            "path": path,
            "headers": headers,
            "query_params": query_params,
            "payload_hash": payload_hash,
            "auth_info": auth_info,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": True, "user_id": user_id}


def test_verify_signature_rejects_invalid_database_backed_signature(db_user, created_rows):
    user_id, username = db_user
    token_key = _insert_test_service_token(user_id, created_rows)
    access_key = f"{username}:{token_key}"

    method = "GET"
    path = "/hydroshare/resource"
    headers = {"host": "localhost", "x-amz-date": "20260701T000000Z"}
    query_params = {"x-id": "GetObject"}
    payload_hash = hashlib.sha256(b"").hexdigest()
    auth_info = _build_sigv4_auth_info(
        method=method,
        path=path,
        headers=headers,
        query_params=query_params,
        payload_hash=payload_hash,
        secret_key=token_key,
        access_key=access_key,
    )
    auth_info["signature"] = auth_info["signature"][:-1] + (
        "0" if auth_info["signature"][-1] != "0" else "1"
    )

    response = client.post(
        "/verify-signature/",
        json={
            "method": method,
            "path": path,
            "headers": headers,
            "query_params": query_params,
            "payload_hash": payload_hash,
            "auth_info": auth_info,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "invalid_signature"}


def test_verify_csrf_rejects_invalid_token_format():
    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": "abc",
            "csrf_token": "not-valid-***",
            "request_method": "GET",
            "request_headers": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "invalid_csrf_token"}


def test_verify_csrf_rejects_invalid_session():
    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": "missing-session",
            "csrf_token": "a" * 32,
            "request_method": "GET",
            "request_headers": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "invalid_session"}


def test_verify_csrf_allows_safe_method_with_valid_db_session(db_user, created_rows):
    user_id, username = db_user
    session_key = _insert_test_session(user_id, created_rows)

    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": session_key,
            "csrf_token": "a" * 32,
            "request_method": "GET",
            "request_headers": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": True, "user_id": user_id, "username": username}


def test_verify_csrf_rejects_missing_request_token_for_unsafe_method(db_user, created_rows):
    user_id, _ = db_user
    session_key = _insert_test_session(user_id, created_rows)

    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": session_key,
            "csrf_token": "a" * 32,
            "request_method": "POST",
            "request_headers": {},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "missing_csrf_token"}


def test_verify_csrf_rejects_mismatch_for_unsafe_method(db_user, created_rows):
    user_id, _ = db_user
    session_key = _insert_test_session(user_id, created_rows)

    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": session_key,
            "csrf_token": "a" * 32,
            "request_method": "POST",
            "request_headers": {"x-csrftoken": "b" * 32},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": False, "reason": "csrf_token_mismatch"}


def test_verify_csrf_allows_matching_token_for_unsafe_method(db_user, created_rows):
    user_id, username = db_user
    session_key = _insert_test_session(user_id, created_rows)

    response = client.post(
        "/verify-csrf/",
        json={
            "session_id": session_key,
            "csrf_token": "a" * 32,
            "request_method": "POST",
            "request_headers": {"x-csrftoken": "a" * 32},
        },
    )

    assert response.status_code == 200
    assert response.json() == {"allow": True, "user_id": user_id, "username": username}
