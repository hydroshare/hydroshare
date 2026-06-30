import logging
import os
import hashlib
import xml.etree.ElementTree as ET
import re
from fastapi import APIRouter, Request, Response
from api.lib.auth_service import verify_csrf_token_sync, verify_signature_sync
from api.lib.authorization import check_s3_authorization
from api.lib.event_service import post_s3_event
from api.lib.s3_auth import (
    get_s3_action_from_request,
    parse_authorization_header,
    parse_presigned_auth_query,
    parse_s3_path,
)
from api.lib.s3_proxy import S3ProxyClient

logger = logging.getLogger("hs_s3_proxy")
DEBUG_HEADERS = os.environ.get("S3_PROXY_DEBUG_HEADERS", "false").lower() == "true"
BACKEND_BUCKET = os.environ.get("S3_BACKEND_BUCKET")

RESOURCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")


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


router = APIRouter()
s3_proxy = S3ProxyClient()


def _get_query_value_case_insensitive(query_params: dict, key: str):
    key_lower = key.lower()
    for k, v in query_params.items():
        if str(k).lower() == key_lower:
            return v
    return None


def _verify_sigv4_request(method, path, headers, query_params, body, auth_info, is_presigned):
    """Validate a SigV4 or presigned request and return the user or an error response."""
    payload_hash = headers.get('x-amz-content-sha256') or headers.get('X-Amz-Content-Sha256')
    if not payload_hash and is_presigned:
        payload_hash = _get_query_value_case_insensitive(query_params, 'X-Amz-Content-Sha256')
    # Presigned GET/HEAD requests commonly use unsigned payload semantics.
    if not payload_hash and is_presigned:
        payload_hash = 'UNSIGNED-PAYLOAD'
    if not payload_hash:
        payload_hash = hashlib.sha256(body if body else b'').hexdigest()

    result = verify_signature_sync(
        method=method, path=path, headers=headers,
        query_params=query_params, payload_hash=payload_hash,
        auth_info=auth_info,
    )
    if result.get("allow"):
        return result.get("user_id"), None

    error = result.get("reason")
    if error == "invalid_signature":
        return None, Response(content=b"<Error><Code>SignatureDoesNotMatch</Code><Message>The request signature we "
                              b"calculated does not match the signature you provided.</Message></Error>",
                              status_code=403, media_type="application/xml")
    if error == "auth_service_error":
        return None, Response(content=b"<Error><Code>InternalError</Code><Message>Internal Server Error</Message>"
                              b"</Error>", status_code=500, media_type="application/xml")
    return None, Response(content=b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>",
                          status_code=403, media_type="application/xml")


def _verify_csrf_session_request(request: Request):
    """Authenticate a request using session and CSRF cookies."""
    csrf_token = request.cookies.get("csrftoken")
    session_id = request.cookies.get("sessionid")
    if not session_id:
        logger.warning("No valid authorization (header/presigned) or session cookie found")
        return None, None, Response(
            content=b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>",
            status_code=403,
            media_type="application/xml",
        )

    logger.info("No SigV4 auth header; attempting CSRF/session authentication.")
    csrf_result = verify_csrf_token_sync(session_id=session_id, csrf_token=csrf_token)
    if not csrf_result.get("allow"):
        reason = csrf_result.get("reason", "unknown")
        if reason == "auth_service_error":
            return None, None, Response(
                content=b"<Error><Code>InternalError</Code><Message>Internal Server Error</Message></Error>",
                status_code=500,
                media_type="application/xml",
            )
        logger.warning(f"CSRF token authentication failed: {reason}")
        return None, None, Response(
            content=b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>",
            status_code=403,
            media_type="application/xml",
        )

    user_id = csrf_result.get("user_id")
    username = csrf_result.get("username", "")
    logger.info(f"CSRF authentication succeeded for user: {username}")
    return user_id, username, None


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.api_route("/{full_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def proxy_s3_request(request: Request, full_path: str):
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

    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)
    is_presigned = False
    if not auth_info:
        auth_info = parse_presigned_auth_query(query_params)
        is_presigned = auth_info is not None

    if auth_info:
        username = auth_info['access_key'].split(":")[0]
        user_id, error_response = _verify_sigv4_request(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body,
            auth_info=auth_info,
            is_presigned=is_presigned,
        )
    else:
        user_id, username, error_response = _verify_csrf_session_request(request)
    if error_response:
        return error_response

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"S3 Action: {action} for user: {username}")

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
        authorized = check_s3_authorization(
            username=username, action=action,
            bucket=authz_bucket, object_path=authz_prefix, prefixes=authz_prefixes,
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return Response(content=b"<Error><Code>InternalError</Code><Message>Internal Server Error</Message></Error>",
                        status_code=500, media_type="application/xml")

    if not authorized:
        logger.warning(f"Access denied for user {username} to {action} on {authz_bucket}/{authz_prefix}")
        return Response(content=b"<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>",
                        status_code=403, media_type="application/xml")

    logger.info(f"Access granted for user {username} to {action} on {authz_bucket}/{authz_prefix}")

    try:
        response = await s3_proxy.proxy_request(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return Response(content=b"<Error><Code>InternalError</Code><Message>Internal Server Error</Message></Error>",
                        status_code=500, media_type="application/xml")

    if action in ["s3:PutObject", "s3:CompleteMultipartUpload"] and response.status_code in [200, 204]:
        raw_size = headers.get("x-amz-decoded-content-length") or headers.get("content-length") or "0"
        try:
            file_size = int(raw_size)
        except (ValueError, TypeError):
            file_size = 0
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=user_id, file_size=file_size,
            zone=s3_proxy.zone_for_bucket(authz_bucket),
        )
    if action in ["s3:DeleteObjects"] and response.status_code in [200, 204]:
        post_s3_event(
            action=action, bucket=authz_bucket, object_path=authz_prefix,
            username=username, user_id=user_id,
            zone=s3_proxy.zone_for_bucket(authz_bucket),
        )
        logger.info(f"Successfully proxied {action} for user {username} on {authz_bucket}/{authz_prefix}")
    return response
