import asyncio
import logging
import os

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from api.database import engine
from api.lib.auth_service import check_authorization
from api.lib.authorization import check_s3_authorization
from api.lib.s3_auth import (
    get_s3_action_from_request,
    parse_authorization_header,
    parse_s3_path,
    verify_signature_v4,
)
from api.lib.s3_proxy import S3ProxyClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hs_auth_proxy")

app = FastAPI(title="HydroShare S3 Auth Proxy")

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


def _validate_token(username: str, method: str, path: str, headers: dict,
                    query_params: dict, body: bytes, auth_info: dict,
                    include_bucket_name: bool = False):
    """Validate username's token against the database and verify the SigV4 signature.

    Returns (token_key, user_id, bucket_name) on success if include_bucket_name is True,
    or (token_key, user_id) otherwise. Returns None on failure along with an error Response.
    """
    if include_bucket_name:
        query = """
        SELECT authtoken_token.key, authtoken_token.user_id, theme_userprofile._bucket_name
        FROM authtoken_token
        INNER JOIN auth_user ON authtoken_token.user_id = auth_user.id
        INNER JOIN theme_userprofile ON auth_user.id = theme_userprofile.user_id
        WHERE auth_user.username = :username
        """
    else:
        query = """
        SELECT authtoken_token.key, authtoken_token.user_id
        FROM authtoken_token
        INNER JOIN auth_user ON authtoken_token.user_id = auth_user.id
        WHERE auth_user.username = :username
        """

    with engine.connect() as conn:
        result = conn.execute(text(query), parameters=dict(username=username))
        row = result.fetchone()

        if not row:
            logger.warning(f"No token found for username: {username}")
            return None, None

        if include_bucket_name:
            token_key, user_id, bucket_name = row
        else:
            token_key, user_id = row
            bucket_name = None

        signature_valid = verify_signature_v4(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body,
            secret_key=token_key, auth_info=auth_info
        )

        if not signature_valid:
            logger.warning(f"Invalid signature for username: {username}")
            return None, "invalid_signature"

        logger.info(f"Authenticated user: {username} (id: {user_id})")

        if include_bucket_name:
            return (token_key, user_id, bucket_name), None
        return (token_key, user_id), None


@app.api_route("/resource/{resource_id}/{rest_of_path:path}", methods=["GET", "PUT", "POST", "DELETE", "HEAD"])
async def proxy_hydroshare_request(request: Request, resource_id: str, rest_of_path: str):
    """HydroShare-native endpoint using token-based auth. Path: /resource/{id}/data/contents/{file}"""
    method = request.method
    headers = dict(request.headers)
    query_params = dict(request.query_params)
    body = await request.body()

    logger.info(f"Received {method} request for resource={resource_id}, path={rest_of_path}")

    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)

    if not auth_info:
        return Response(
            content=b'{"error": "Authentication required"}',
            status_code=401, media_type="application/json"
        )

    username = auth_info['access_key']

    try:
        token_result, error = _validate_token(
            username, method, f"/resource/{resource_id}/{rest_of_path}",
            headers, query_params, body, auth_info, include_bucket_name=True
        )
    except Exception as e:
        logger.error(f"Database error validating token: {e}", exc_info=True)
        return Response(
            content=b'{"error": "Internal server error"}',
            status_code=500, media_type="application/json"
        )

    if token_result is None:
        if error == "invalid_signature":
            return Response(
                content=b'{"error": "Invalid signature"}',
                status_code=401, media_type="application/json"
            )
        return Response(
            content=b'{"error": "Invalid credentials"}',
            status_code=401, media_type="application/json"
        )

    _, user_id, bucket_name = token_result

    if method == "GET":
        action = "s3:GetObject"
    elif method == "PUT":
        action = "s3:PutObject"
    elif method == "DELETE":
        action = "s3:DeleteObject"
    elif method == "HEAD":
        action = "s3:HeadObject"
    else:
        action = "s3:Unknown"

    object_path = f"{resource_id}/{rest_of_path}"

    try:
        auth_bucket = os.environ.get("S3_BACKEND_BUCKET", "hydroshare")
        authorized = await check_authorization(
            username=username, action=action, bucket=auth_bucket,
            object_path=object_path, prefixes=[object_path]
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return Response(
            content=b'{"error": "Internal server error"}',
            status_code=500, media_type="application/json"
        )

    if not authorized:
        logger.warning(f"Access denied for user {bucket_name} to {action} on resource {resource_id}")
        return Response(
            content=b'{"error": "Access denied"}',
            status_code=403, media_type="application/json"
        )

    logger.info(f"Access granted for user {username} to {action} on resource {resource_id}")

    use_single_bucket = os.environ.get("USE_SINGLE_BUCKET", "false").lower() == "true"
    if use_single_bucket:
        backend_bucket = os.environ.get("S3_BACKEND_BUCKET", "hydroshare-beta-micro-auth-proxy")
        backend_path = f"/{backend_bucket}/{resource_id}/{rest_of_path}"
    else:
        backend_path = f"/{resource_id}/{rest_of_path}"

    try:
        return await s3_proxy.proxy_request(
            method=method, path=backend_path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return Response(
            content=b'{"error": "Internal server error"}',
            status_code=500, media_type="application/json"
        )


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

    auth_header = headers.get('authorization', '')
    auth_info = parse_authorization_header(auth_header)

    if not auth_info:
        logger.warning("No valid authorization header found")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    username = auth_info['access_key']

    try:
        token_result, error = _validate_token(
            username, method, path, headers, query_params, body, auth_info
        )
    except Exception as e:
        logger.error(f"Database error validating token: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if token_result is None:
        if error == "invalid_signature":
            return Response(content=XML_SIGNATURE_MISMATCH, status_code=403, media_type="application/xml")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    _, user_id = token_result

    action = get_s3_action_from_request(method, path, query_params)
    logger.info(f"S3 Action: {action} for user: {username}")

    try:
        authorized = check_s3_authorization(
            username=username, action=action,
            bucket=bucket or "", object_path=object_path or ""
        )
    except Exception as e:
        logger.error(f"Error checking authorization: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")

    if not authorized:
        logger.warning(f"Access denied for user {username} to {action} on {bucket}/{object_path}")
        return Response(content=XML_ACCESS_DENIED, status_code=403, media_type="application/xml")

    logger.info(f"Access granted for user {username} to {action} on {bucket}/{object_path}")

    try:
        return await s3_proxy.proxy_request(
            method=method, path=path, headers=headers,
            query_params=query_params, body=body if body else None
        )
    except Exception as e:
        logger.error(f"Error proxying request: {e}", exc_info=True)
        return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"service": "HydroShare S3 Auth Proxy", "status": "running"}


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
