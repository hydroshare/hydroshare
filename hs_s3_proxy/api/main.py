import asyncio
import hashlib
import logging
import os

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from api.lib.auth_service import verify_signature_sync
from api.lib.authorization import check_s3_authorization
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

# When set, the proxy serves exactly this one backend bucket. Client-facing S3
# URLs address it directly (S3-native), and keys underneath follow the layout
# {user_bucket}/{resource_id}/{rest}. The {user_bucket}/ prefix is peeled off
# before calling micro-auth, which expects {resource_id}/... as the prefix.
BACKEND_BUCKET = os.environ.get("S3_BACKEND_BUCKET")

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
    """Delegate SigV4 verification to micro-auth.

    Returns (user_id, None) on success, or (None, reason) on failure.
    """
    payload_hash = hashlib.sha256(body if body else b'').hexdigest()
    result = verify_signature_sync(
        method=method, path=path, headers=headers,
        query_params=query_params, payload_hash=payload_hash,
        auth_info=auth_info,
    )
    if result.get("allow"):
        return result.get("user_id"), None
    return None, result.get("reason")


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

    path = f"/{full_path}"
    bucket, object_path = parse_s3_path(path)
    logger.info(f"Received {method} request for bucket={bucket}, object={object_path}")

    if BACKEND_BUCKET and bucket and bucket != BACKEND_BUCKET:
        logger.warning(f"Request addressed bucket={bucket}, but this proxy serves {BACKEND_BUCKET}")
        return Response(content=XML_NO_SUCH_BUCKET, status_code=404, media_type="application/xml")

    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)

    if not auth_info:
        logger.warning("No valid authorization header found")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

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

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"S3 Action: {action} for user: {username}")

    if BACKEND_BUCKET and bucket == BACKEND_BUCKET:
        # Key is {user_bucket}/{resource_id}/{rest}. Peel the user_bucket off for
        # authz — micro-auth expects bucket={user_bucket}, prefix={resource_id}/...
        authz_bucket, _, authz_prefix = (object_path or "").partition("/")
    else:
        authz_bucket = bucket or ""
        authz_prefix = object_path or ""

    try:
        authorized = check_s3_authorization(
            username=username, action=action,
            bucket=authz_bucket, object_path=authz_prefix,
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if not authorized:
        logger.warning(f"Access denied for user {username} to {action} on {authz_bucket}/{authz_prefix}")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    logger.info(f"Access granted for user {username} to {action} on {authz_bucket}/{authz_prefix}")

    try:
        return await s3_proxy.proxy_request(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        return super().handle_exit(sig, frame)


async def main():
    server = Server(
        config=uvicorn.Config(
            app, workers=1, loop="asyncio",
            host="0.0.0.0", port=9000, forwarded_allow_ips="*"
        )
    )
    api = asyncio.create_task(server.serve())
    await asyncio.wait([api])


if __name__ == "__main__":
    asyncio.run(main())
