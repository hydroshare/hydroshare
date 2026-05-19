from fastapi import APIRouter, Request, Response

from api.lib.auth_service import verify_csrf_token_sync
from api.lib.authorization import check_s3_authorization
from api.lib.event_service import post_s3_event
from api.lib.s3_auth import (
    get_s3_action_from_request,
    parse_authorization_header,
    parse_s3_path,
)
from api.routes.shared import (
    BACKEND_BUCKET,
    RESOURCE_ID_RE,
    XML_ACCESS_DENIED,
    XML_SIGNATURE_MISMATCH,
    internal_error_response,
    log_debug_headers,
    logger,
    parse_delete_object_keys,
    s3_proxy,
    validate_token,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "healthy"}


@router.get("/")
async def root():
    return {"service": "HydroShare S3 Proxy", "status": "running"}


@router.api_route("/{full_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def proxy_s3_request(request: Request, full_path: str):
    """Generic S3 proxy endpoint that handles all S3 requests."""
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    body = await request.body()

    log_debug_headers(request, method, full_path)

    path = f"/{full_path}"
    bucket, object_path = parse_s3_path(path)
    object_path = query_params.get("prefix", object_path)
    logger.info(f"Received {method} request for bucket={bucket}, object={object_path}")

    if BACKEND_BUCKET and bucket and bucket != BACKEND_BUCKET:
        # Probe/misdirected request (e.g. mc endpoint-style detection).
        # Forward to the backend so it returns a proper S3 NoSuchBucket error
        # that S3 clients recognise. No auth layer needed - the backend will
        # reject the unknown bucket itself.
        logger.debug(f"Request addressed bucket={bucket}, forwarding probe to backend (serves {BACKEND_BUCKET})")
        try:
            return await s3_proxy.proxy_request(
                method=method,
                path=path,
                headers=headers,
                query_params=query_params,
                body=body if body else None,
            )
        except Exception as e:
            logger.error(f"Error proxying probe request: {e}", exc_info=True)
            return internal_error_response()

    auth_header = headers.get("authorization", "")
    auth_info = parse_authorization_header(auth_header)

    # SigV4 path.
    if auth_info:
        username = auth_info["access_key"]
        user_id, error = validate_token(method, path, headers, query_params, body, auth_info)
        if user_id is None:
            if error == "invalid_signature":
                return Response(content=XML_SIGNATURE_MISMATCH, status_code=403, media_type="application/xml")
            if error == "auth_service_error":
                return internal_error_response()
            return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    # CSRF cookie path.
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
                return internal_error_response()
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
            # authz - hs-s3-auth expects bucket={user_bucket}, prefix={resource_id}/...
            authz_bucket = path_parts[0]
            authz_prefix = "/".join(path_parts[1:])

    authz_prefixes = None
    if action == "s3:DeleteObjects":
        authz_prefixes = parse_delete_object_keys(body)
        if len(authz_prefixes) == 1:
            authz_prefix = authz_prefixes[0]

    try:
        authorized = check_s3_authorization(
            username=username,
            action=action,
            bucket=authz_bucket,
            object_path=authz_prefix,
            prefixes=authz_prefixes,
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return internal_error_response()

    if not authorized:
        logger.warning(f"Access denied for user {username} to {action} on {authz_bucket}/{authz_prefix}")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    logger.info(f"Access granted for user {username} to {action} on {authz_bucket}/{authz_prefix}")

    try:
        response = await s3_proxy.proxy_request(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body if body else None,
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return internal_error_response()

    if action in ["s3:PutObject", "s3:CompleteMultipartUpload"] and response.status_code in [200, 204]:
        raw_size = headers.get("x-amz-decoded-content-length") or headers.get("content-length") or "0"
        try:
            file_size = int(raw_size)
        except (ValueError, TypeError):
            file_size = 0
        post_s3_event(
            action=action,
            bucket=authz_bucket,
            object_path=authz_prefix,
            username=username,
            user_id=user_id,
            file_size=file_size,
        )
    if action in ["s3:DeleteObjects"] and response.status_code in [200, 204]:
        post_s3_event(
            action=action,
            bucket=authz_bucket,
            object_path=authz_prefix,
            username=username,
            user_id=user_id,
        )
        logger.info(f"Successfully proxied {action} for user {username} on {authz_bucket}/{authz_prefix}")
    return response
