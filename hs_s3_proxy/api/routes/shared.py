import hashlib
import logging
import os
import re
import xml.etree.ElementTree as ET

from fastapi import Request, Response

from api.lib.auth_service import verify_signature_sync
from api.lib.s3_proxy import S3ProxyClient

logger = logging.getLogger("hs_s3_proxy")
DEBUG_HEADERS = os.environ.get("S3_PROXY_DEBUG_HEADERS", "false").lower() == "true"

# When set, the proxy serves exactly this one backend bucket. Client-facing S3
# URLs address it directly (S3-native). Keys may follow either
# {resource_id}/{rest} or {user_bucket}/{resource_id}/{rest}. In the latter
# case, the {user_bucket}/ prefix is peeled off before calling hs-s3-auth,
# which expects {resource_id}/... as the prefix.
#
# If multi-zone config is present, this single-bucket guard is disabled.
_MULTI_ZONE_CONFIG = os.environ.get("S3_BACKEND_ZONES_CONFIG") or os.environ.get("RESOURCE_S3_ZONES_CONFIG")
BACKEND_BUCKET = None if _MULTI_ZONE_CONFIG else os.environ.get("S3_BACKEND_BUCKET")
RESOURCE_ID_RE = re.compile(r"^[0-9a-f]{32}$")

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


def validate_token(method: str, path: str, headers: dict,
                   query_params: dict, body: bytes, auth_info: dict):
    """Delegate SigV4 verification to hs-s3-auth.

    Returns (user_id, None) on success, or (None, reason) on failure.
    """
    payload_hash = headers.get("x-amz-content-sha256") or headers.get("X-Amz-Content-Sha256")
    if not payload_hash:
        payload_hash = hashlib.sha256(body if body else b"").hexdigest()
    result = verify_signature_sync(
        method=method,
        path=path,
        headers=headers,
        query_params=query_params,
        payload_hash=payload_hash,
        auth_info=auth_info,
    )
    if result.get("allow"):
        return result.get("user_id"), None
    return None, result.get("reason")


def parse_delete_object_keys(body: bytes) -> list[str]:
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


def log_debug_headers(request: Request, method: str, full_path: str) -> None:
    if not DEBUG_HEADERS:
        return

    cookie_names = sorted(request.cookies.keys())
    cookie_lengths = {name: len(value or "") for name, value in request.cookies.items()}
    logger.info(
        "Proxy request debug: method=%s path=/%s cookie_names=%s cookie_lengths=%s",
        method,
        full_path,
        cookie_names,
        cookie_lengths,
    )


def internal_error_response() -> Response:
    return Response(content=XML_INTERNAL_ERROR, status_code=500, media_type="application/xml")
