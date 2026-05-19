from fastapi import APIRouter, Request

from api.lib.event_service import post_s3_event
from api.lib.s3_auth import (
    get_s3_action_from_request,
    parse_authorization_header,
    parse_s3_path,
)
from api.routes.shared import (
    RESOURCE_ID_RE,
    internal_error_response,
    logger,
    parse_delete_object_keys,
    s3_proxy,
)

router = APIRouter()


@router.get("/health")
async def internal_health_check():
    return {"status": "healthy"}


@router.api_route("/{full_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def internal_proxy_s3_request(request: Request, full_path: str):
    """Internal S3 proxy - skips auth verification, passes credentials to backend, fires events."""
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
    auth_header = headers.get("authorization", "")
    auth_info = parse_authorization_header(auth_header)
    username = auth_info["access_key"]

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"[internal] S3 Action: {action} for user: {username}")

    authz_bucket = bucket or ""
    authz_prefix = object_path or ""
    path_parts = (object_path or "").split("/", 2)
    if len(path_parts) >= 2 and RESOURCE_ID_RE.fullmatch(path_parts[1]):
        authz_bucket = path_parts[0]
        authz_prefix = "/".join(path_parts[1:])

    authz_prefixes = None
    if action == "s3:DeleteObjects":
        authz_prefixes = parse_delete_object_keys(body)
        if len(authz_prefixes) == 1:
            authz_prefix = authz_prefixes[0]

    try:
        response = await s3_proxy.proxy_request(
            method=method,
            path=path,
            headers=headers,
            query_params=query_params,
            body=body if body else None,
        )
    except Exception as e:
        logger.error(f"[internal] Error proxying request: {e}", exc_info=True)
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
            user_id=None,
            file_size=file_size,
        )
    if action in ["s3:DeleteObjects"] and response.status_code in [200, 204]:
        post_s3_event(
            action=action,
            bucket=authz_bucket,
            object_path=authz_prefix,
            username=username,
            user_id=None,
        )
        logger.info(f"[internal] Successfully proxied {action} for user {username} on {authz_bucket}/{authz_prefix}")
    return response
