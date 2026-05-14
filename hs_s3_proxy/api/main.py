import asyncio
import hashlib
import logging
import os
import re
import xml.etree.ElementTree as ET

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from api.lib.auth_service import verify_csrf_token_sync, verify_signature_sync
from api.lib.authorization import check_s3_authorization
from api.lib.event_service import post_s3_event
from api.lib.s3_auth import (
    get_s3_action_from_request,
    parse_authorization_header,
    parse_s3_path,
)
from api.lib.s3_proxy import S3ProxyClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hs_s3_proxy")
DEBUG_HEADERS = os.environ.get("S3_PROXY_DEBUG_HEADERS", "false").lower() == "true"

# When set, the proxy serves exactly this one backend bucket. Client-facing S3
# URLs address it directly (S3-native). Keys may follow either
# {resource_id}/{rest} or {user_bucket}/{resource_id}/{rest}. In the latter
# case, the {user_bucket}/ prefix is peeled off before calling hs-s3-auth,
# which expects {resource_id}/... as the prefix.
BACKEND_BUCKET = os.environ.get("S3_BACKEND_BUCKET")
RESOURCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")

app = FastAPI(title="HydroShare S3 Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3_proxy = S3ProxyClient()

XML_ACCESS_DENIED = (
    b"<?xml version='1.0' encoding='UTF-8'?>"
    b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>"
)
XML_INTERNAL_ERROR = (
    b"<?xml version='1.0' encoding='UTF-8'?>"
    b"<Error><Code>InternalError</Code><Message>Internal Server Error</Message></Error>"
)
XML_SIGNATURE_MISMATCH = (
    b"<?xml version='1.0' encoding='UTF-8'?>"
    b"<Error><Code>SignatureDoesNotMatch</Code>"
    b"<Message>The request signature we calculated does not match the signature you provided.</Message></Error>"
)
XML_NO_SUCH_BUCKET = (
    b"<?xml version='1.0' encoding='UTF-8'?>"
    b"<Error><Code>NoSuchBucket</Code>"
    b"<Message>The specified bucket is not served by this endpoint.</Message></Error>"
)


def _validate_token(method: str, path: str, headers: dict,
                    query_params: dict, body: bytes, auth_info: dict):
    """Delegate SigV4 verification to hs-s3-auth.

    Returns (user_id, None) on success, or (None, reason) on failure.
    """
    payload_hash = headers.get('x-amz-content-sha256') or headers.get('X-Amz-Content-Sha256')
    if not payload_hash:
        payload_hash = hashlib.sha256(body if body else b'').hexdigest()
    result = verify_signature_sync(
        method=method, path=path, headers=headers,
        query_params=query_params, payload_hash=payload_hash,
        auth_info=auth_info,
    )
    if result.get("allow"):
        return result.get("user_id"), None
    return None, result.get("reason")


def _parse_delete_object_keys(body: bytes) -> list[str]:
    if not body:
        return []

    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        logger.warning("Failed to parse DeleteObjects request body")
        return []

    keys = []
    for obj in root.findall("{*}Object"):
        key = obj.findtext("{*}Key")
        if key:
            keys.append(key)
    return keys


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"service": "HydroShare S3 Proxy", "status": "running"}


@app.api_route("/{full_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def proxy_s3_request(request: Request, full_path: str):
    """Generic S3 proxy endpoint that handles all S3 requests."""
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    body = await request.body()

    if DEBUG_HEADERS:
        cookie_names = sorted(request.cookies.keys())
        cookie_lengths = {name: len(value or "") for name, value in request.cookies.items()}
        logger.info(
            "Proxy request debug: method=%s path=/%s cookie_names=%s cookie_lengths=%s",
            method,
            full_path,
            cookie_names,
            cookie_lengths,
        )

    path = f"/{full_path}"
    bucket, object_path = parse_s3_path(path)
    object_path = query_params.get("prefix", object_path)
    logger.info(f"Received {method} request for bucket={bucket}, object={object_path}")

    if BACKEND_BUCKET and bucket and bucket != BACKEND_BUCKET:
        # Probe/misdirected request (e.g. mc endpoint-style detection).
        # Forward to the backend so it returns a proper S3 NoSuchBucket error
        # that S3 clients recognise. No auth layer needed — the backend will
        # reject the unknown bucket itself.
        logger.debug(f"Request addressed bucket={bucket}, forwarding probe to backend (serves {BACKEND_BUCKET})")
        try:
            return await s3_proxy.proxy_request(
                method=method, path=path, headers=headers,
                query_params=query_params, body=body if body else None,
            )
        except Exception as e:
            logger.error(f"Error proxying probe request: {e}", exc_info=True)
            return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)

    # --- SigV4 path ---
    if auth_info:
        username = auth_info['access_key']
        user_id, error = _validate_token(
            method, path, headers, query_params, body, auth_info
        )
        if user_id is None:
            if error == "invalid_signature":
                return Response(content=XML_SIGNATURE_MISMATCH, status_code=403, media_type="application/xml")
            if error == "auth_service_error":
                return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")
            return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    # --- CSRF cookie path ---
    else:
        csrf_token = request.cookies.get("csrftoken")
        session_id = request.cookies.get("sessionid")
        if not session_id:
            logger.warning("No valid authorization header or session cookie found")
            return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

        logger.info("No SigV4 auth header; attempting CSRF/session authentication.")
        csrf_result = verify_csrf_token_sync(session_id=session_id, csrf_token=csrf_token)
        if not csrf_result.get("allow"):
            reason = csrf_result.get("reason", "unknown")
            if reason == "auth_service_error":
                return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")
            logger.warning(f"CSRF token authentication failed: {reason}")
            return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

        user_id = csrf_result.get("user_id")
        username = csrf_result.get("username", "")
        logger.info(f"CSRF authentication succeeded for user: {username}")

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"S3 Action: {action} for user: {username}")

    authz_bucket = bucket or ""
    authz_prefix = object_path or ""
    if BACKEND_BUCKET and bucket == BACKEND_BUCKET:
        path_parts = (object_path or "").split("/", 2)
        if len(path_parts) >= 2 and RESOURCE_ID_RE.fullmatch(path_parts[1]):
            # Key is {user_bucket}/{resource_id}/{rest}. Peel the user_bucket off for
            # authz — hs-s3-auth expects bucket={user_bucket}, prefix={resource_id}/...
            authz_bucket = path_parts[0]
            authz_prefix = "/".join(path_parts[1:])

    authz_prefixes = None
    if action == "s3:DeleteObjects":
        authz_prefixes = _parse_delete_object_keys(body)
        if len(authz_prefixes) == 1:
            authz_prefix = authz_prefixes[0]

    try:
        authorized = check_s3_authorization(
            username=username, action=action,
            bucket=authz_bucket, object_path=authz_prefix, prefixes=authz_prefixes,
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if not authorized:
        logger.warning(f"Access denied for user {username} to {action} on {authz_bucket}/{authz_prefix}")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    logger.info(f"Access granted for user {username} to {action} on {authz_bucket}/{authz_prefix}")

    try:
        response = await s3_proxy.proxy_request(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if action in ["s3:PutObject", "s3:CompleteMultipartUpload"] and response.status_code in [200, 204]:
        raw_size = headers.get("x-amz-decoded-content-length") or headers.get("content-length") or "0"
        try:
            file_size = int(raw_size)
        except (ValueError, TypeError):
            file_size = 0
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=user_id, file_size=file_size,
        )
    if action in ["s3:DeleteObjects"] and response.status_code in [200, 204]:
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=user_id,
        )
        logger.info(f"Successfully proxied {action} for user {username} on {authz_bucket}/{authz_prefix}")
    return response


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)


# ---------------------------------------------------------------------------
# Internal proxy app (port 9001) — no auth layer, events still fired.
# Only reachable inside the Docker network; never exposed externally.
# ---------------------------------------------------------------------------

internal_app = FastAPI(title="HydroShare S3 Proxy (internal)")

internal_app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@internal_app.get("/health")
async def internal_health_check():
    return {"status": "healthy"}


@internal_app.api_route("/{full_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def internal_proxy_s3_request(request: Request, full_path: str):
    """Internal S3 proxy — skips auth verification, passes credentials to backend, fires events."""
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    body = await request.body()

    path = f"/{full_path}"
    bucket, object_path = parse_s3_path(path)
    object_path = query_params.get("prefix", object_path)
    logger.info(f"[internal] Received {method} request for bucket={bucket}, object={object_path}")

    # Derive the acting username from the Authorization header if present,
    # otherwise fall back to the configured backend access key (e.g. cuahsi).
    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)
    username = auth_info['access_key'] if auth_info else s3_proxy.backend_access_key

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"[internal] S3 Action: {action} for user: {username}")

    authz_bucket = bucket or ""
    authz_prefix = object_path or ""
    if BACKEND_BUCKET and bucket == BACKEND_BUCKET:
        path_parts = (object_path or "").split("/", 2)
        if len(path_parts) >= 2 and RESOURCE_ID_RE.fullmatch(path_parts[1]):
            authz_bucket = path_parts[0]
            authz_prefix = "/".join(path_parts[1:])

    authz_prefixes = None
    if action == "s3:DeleteObjects":
        authz_prefixes = _parse_delete_object_keys(body)
        if len(authz_prefixes) == 1:
            authz_prefix = authz_prefixes[0]

    try:
        response = await s3_proxy.proxy_request(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"[internal] Error proxying request: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if action in ["s3:PutObject", "s3:CompleteMultipartUpload"] and response.status_code in [200, 204]:
        raw_size = headers.get("x-amz-decoded-content-length") or headers.get("content-length") or "0"
        try:
            file_size = int(raw_size)
        except (ValueError, TypeError):
            file_size = 0
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=None, file_size=file_size,
        )
    if action in ["s3:DeleteObjects"] and response.status_code in [200, 204]:
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=None,
        )
        logger.info(f"[internal] Successfully proxied {action} for user {username} on {authz_bucket}/{authz_prefix}")
    return response


async def main():
    external_server = Server(
        config=uvicorn.Config(
            app, workers=1, loop="asyncio",
            host="0.0.0.0", port=9000, forwarded_allow_ips="*"
        )
    )
    internal_server = Server(
        config=uvicorn.Config(
            internal_app, workers=1, loop="asyncio",
            host="0.0.0.0", port=9001, forwarded_allow_ips="*"
        )
    )
    await asyncio.wait([
        asyncio.create_task(external_server.serve()),
        asyncio.create_task(internal_server.serve()),
    ])


if __name__ == "__main__":
    asyncio.run(main())
