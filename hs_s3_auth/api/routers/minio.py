import logging
import os
import string
import hmac
from typing import AnyStr, Dict, List, Optional
from urllib.parse import urlparse

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.cache import (
    backfill_edit_access,
    backfill_resource_discoverability,
    backfill_superuser_and_id,
    backfill_view_access,
    # is_superuser_and_id_cache,
    # resource_discoverability_cache,
    # user_has_edit_access_cache,
    # user_has_view_access_cache,
)
from api.database import (
    get_user_by_session_id,
    get_user_service_account_secrets_and_id,
    is_superuser_and_id,
    resource_discoverability,
    user_has_edit_access,
    user_has_view_access,
    quota_is_exceeded
)
from api.sigv4 import verify_signature_v4


router = APIRouter()
logger = logging.getLogger("hs-s3-auth")
_CSRF_CHARS = string.ascii_letters + string.digits
CSRF_ALLOWED_CHARS = set(_CSRF_CHARS)
CSRF_SECRET_LENGTH = 32
CSRF_TOKEN_LENGTH = 64
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}


def _lower_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    return {str(k).lower(): str(v) for k, v in (headers or {}).items()}


def _unmask_cipher_token(token: str) -> str:
    mask = token[:CSRF_SECRET_LENGTH]
    cipher = token[CSRF_SECRET_LENGTH:]
    chars = _CSRF_CHARS
    char_map = {c: i for i, c in enumerate(chars)}
    return "".join(chars[(char_map[c] - char_map[m]) % len(chars)] for c, m in zip(cipher, mask))


def _normalize_csrf_secret(secret: str) -> Optional[str]:
    if not _is_valid_csrf_token(secret):
        return None
    if len(secret) == CSRF_TOKEN_LENGTH:
        return _unmask_cipher_token(secret)
    return secret


def _does_token_match(request_csrf_token: str, csrf_secret: str) -> bool:
    if len(request_csrf_token) == CSRF_TOKEN_LENGTH:
        request_csrf_token = _unmask_cipher_token(request_csrf_token)
    return hmac.compare_digest(request_csrf_token, csrf_secret)


def _is_same_domain(host: str, pattern: str) -> bool:
    host = (host or "").split(":", 1)[0].lower()
    pattern = (pattern or "").split(":", 1)[0].lower()
    if not host or not pattern:
        return False
    if pattern.startswith("."):
        pattern = pattern[1:]
    return host == pattern or host.endswith(f".{pattern}")


def _get_trusted_origins() -> List[str]:
    raw = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _origin_verified(headers: Dict[str, str], is_secure: bool) -> bool:
    origin = headers.get("origin")
    if not origin:
        return True

    trusted_origins = _get_trusted_origins()
    host = headers.get("x-forwarded-host") or headers.get("host", "")
    scheme = headers.get("x-forwarded-proto") or ("https" if is_secure else "http")
    good_origin = f"{scheme}://{host}"
    if origin == good_origin:
        return True

    if origin in trusted_origins:
        return True

    try:
        parsed_origin = urlparse(origin)
    except ValueError:
        return False
    if not parsed_origin.scheme or not parsed_origin.netloc:
        return False

    origin_host = parsed_origin.netloc
    for trusted in trusted_origins:
        try:
            parsed_trusted = urlparse(trusted)
        except ValueError:
            continue
        if not parsed_trusted.scheme or not parsed_trusted.netloc:
            continue
        if parsed_trusted.scheme != parsed_origin.scheme:
            continue
        trusted_host = parsed_trusted.netloc
        if trusted_host.startswith("*."):
            if _is_same_domain(origin_host, trusted_host[2:]):
                return True
        elif origin_host.lower() == trusted_host.lower():
            return True

    return False


def _check_referer(headers: Dict[str, str], is_secure: bool) -> bool:
    if not is_secure:
        return True

    referer = headers.get("referer")
    if not referer:
        return False

    try:
        parsed = urlparse(referer)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.netloc:
        return False

    referer_host = parsed.netloc

    for trusted in _get_trusted_origins():
        try:
            parsed_trusted = urlparse(trusted)
        except ValueError:
            continue
        if not parsed_trusted.netloc:
            continue
        trusted_host = parsed_trusted.netloc
        if trusted_host.startswith("*."):
            if _is_same_domain(referer_host, trusted_host[2:]):
                return True
        elif _is_same_domain(referer_host, trusted_host):
            return True

    cookie_domain = os.environ.get("COOKIE_DOMAIN", "").strip()
    good_host = cookie_domain or headers.get("x-forwarded-host") or headers.get("host", "")
    return _is_same_domain(referer_host, good_host)


def _extract_request_csrf_token(headers: Dict[str, str]) -> str:
    return headers.get("x-csrftoken") or headers.get("x-csrf-token") or ""


def _is_valid_csrf_token(token: str) -> bool:
    """Validate Django CSRF token shape (masked or unmasked)."""
    if not token:
        return False
    if len(token) not in (CSRF_SECRET_LENGTH, CSRF_TOKEN_LENGTH):
        return False
    return all(ch in CSRF_ALLOWED_CHARS for ch in token)


class CsrfVerifyRequest(BaseModel):
    session_id: str
    csrf_token: str
    request_method: str = "GET"
    request_headers: Dict[str, str] = Field(default_factory=dict)


@router.post("/verify-csrf/")
async def verify_csrf(request: CsrfVerifyRequest):
    """Authenticate a browser request using the Django session cookie.

    The caller must supply ``session_id`` (the value of the ``sessionid``
    cookie) and ``csrf_token`` (the CSRF token value carried by the browser
    cookie or request).
    """
    headers = _lower_headers(request.request_headers)
    method = (request.request_method or "GET").upper()
    is_secure = (headers.get("x-forwarded-proto") or "").lower() == "https"

    if not _is_valid_csrf_token(request.csrf_token):
        logger.warning("CSRF/session verification failed: invalid CSRF token format")
        return {"allow": False, "reason": "invalid_csrf_token"}

    csrf_secret = _normalize_csrf_secret(request.csrf_token)
    if not csrf_secret:
        logger.warning("CSRF/session verification failed: invalid CSRF secret")
        return {"allow": False, "reason": "invalid_csrf_token"}

    result = get_user_by_session_id(request.session_id)
    if not result:
        logger.warning("CSRF/session verification failed: session not found or expired")
        return {"allow": False, "reason": "invalid_session"}

    user_id, username = result

    if method not in SAFE_METHODS:
        if not _origin_verified(headers, is_secure=is_secure):
            logger.warning("CSRF/session verification failed: bad origin")
            return {"allow": False, "reason": "bad_origin"}

        if not headers.get("origin") and not _check_referer(headers, is_secure=is_secure):
            logger.warning("CSRF/session verification failed: bad referer")
            return {"allow": False, "reason": "bad_referer"}

        request_csrf_token = _extract_request_csrf_token(headers)
        if not request_csrf_token:
            logger.warning("CSRF/session verification failed: missing request CSRF token")
            return {"allow": False, "reason": "missing_csrf_token"}
        if not _is_valid_csrf_token(request_csrf_token):
            logger.warning("CSRF/session verification failed: invalid request CSRF token format")
            return {"allow": False, "reason": "invalid_csrf_token"}
        if not _does_token_match(request_csrf_token, csrf_secret):
            logger.warning("CSRF/session verification failed: CSRF token mismatch")
            return {"allow": False, "reason": "csrf_token_mismatch"}

    logger.info(f"CSRF/cookie authentication succeeded for user: {username} (id={user_id})")
    return {"allow": True, "user_id": user_id, "username": username}


def _parse_action_list(env_var: str, default: str) -> List[str]:
    return [action.strip() for action in os.environ.get(env_var, default).split(",") if action.strip()]


VIEW_ACTIONS = _parse_action_list(
    "S3_VIEW_ACTIONS",
    "s3:GetObject,s3:ListObjects,s3:ListObjectsV2,s3:ListBucket,s3:GetObjectRetention,s3:GetObjectLegalHold,\
        s3:HeadObject",
)
WRITE_ACTIONS = _parse_action_list(
    "S3_WRITE_ACTIONS", "s3:PutObject,s3:CreateMultipartUpload,s3:UploadPart,"
    "s3:CompleteMultipartUpload,s3:PutObjectLegalHold"
)
DELETE_ACTIONS = _parse_action_list(
    "S3_DELETE_ACTIONS", "s3:DeleteObject,s3:DeleteObjects,s3:AbortMultipartUpload"
)
EDIT_ACTIONS = WRITE_ACTIONS + DELETE_ACTIONS


class AllowBaseModel(BaseModel, extra='allow'):
    pass


class Conditions(AllowBaseModel):
    preferred_username: Optional[List[AnyStr]] = []
    username: Optional[List[AnyStr]] = []
    Prefix: Optional[List[AnyStr]] = []
    prefix: Optional[List[AnyStr]] = []

    @property
    def users(self):
        if self.preferred_username:
            return self.preferred_username
        else:
            return self.username

    @property
    def user(self):
        users = self.users
        if len(users) != 1:
            logger.warning(f"Exactly one user must be specified {users}")
            raise ValueError("Exactly one user must be specified")
        return self.users[0]

    @property
    def prefixes(self):
        if self.Prefix:
            return [prefix for prefix in self.Prefix if prefix]
        elif self.prefix:
            return [prefix for prefix in self.prefix if prefix]
        else:
            return []


class Input(AllowBaseModel):
    conditions: Conditions
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    action: AnyStr
    bucket: AnyStr
    object: AnyStr


class AuthRequest(AllowBaseModel):
    input: Input


@router.post("/authorization/")
async def hs_s3_authorization_check(auth_request: AuthRequest):

    username = auth_request.input.conditions.user
    bucket = auth_request.input.bucket
    action = auth_request.input.action

    if username == "cuahsi":
        # allow cuahsi admin account always
        return {"result": {"allow": True}}

    if auth_request.input.action in ["s3:GetBucketLocation", "s3:GetBucketObjectLockConfiguration"]:
        # This is needed by mc to list buckets and does not contain a prefix
        return {"result": {"allow": True}}

    try:
        user_is_superuser, user_id = is_superuser_and_id(username)
    except Exception:
        user_is_superuser, user_id = is_superuser_and_id(username)
        backfill_superuser_and_id(username, user_is_superuser, user_id)
    if user_is_superuser:
        return {"result": {"allow": True}}

    # users access the objects in these buckets through presigned urls, admins
    # are approved above
    if bucket in ["zips", "tmp", "bags"]:
        return {"result": {"allow": False}}

    # prefixes are paths to (folders/set of) objects in the bucket
    prefixes = auth_request.input.conditions.prefixes
    if not prefixes:
        if auth_request.input.object:
            # if there is an object but no prefix, it is a file in the root of
            # the bucket
            prefixes = [auth_request.input.object]
        else:
            return {"result": {"allow": False}}

    # extracted metadata has a prefix of "md/resource_id" and should be view
    # only
    resource_ids_and_is_contents_path = [
        (prefix.split(
            "/")[0], True) if (prefix.split("/", 1)[1].startswith("data/contents/")
                               or prefix.split("/", 1)[1].startswith(".hsmetadata/")) else (prefix.split("/")[0], False)
        for prefix in prefixes
    ]
    # check the user and each resource against the action
    for resource_id, is_contents_path in resource_ids_and_is_contents_path:
        if not _check_user_authorization(user_id, resource_id, action, is_contents_path):
            return {"result": {"allow": False}}
    if resource_ids_and_is_contents_path:
        return {"result": {"allow": True}}

    return {"result": {"allow": False}}


def _check_user_authorization(user_id, resource_id, action, is_contents_path):
    # Break this down into just view and edit for now.
    # We may need to make owners distinct from edit at some point

    # List of actions
    # https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html

    # view actions
    if action in VIEW_ACTIONS:
        try:
            public, allow_private_sharing, discoverable = resource_discoverability(
                resource_id)
        except Exception:
            public, allow_private_sharing, discoverable = resource_discoverability(
                resource_id)
            backfill_resource_discoverability(
                resource_id, public, allow_private_sharing, discoverable)

        try:
            view_access = user_has_view_access(user_id, resource_id)
        except Exception:
            view_access = user_has_view_access(user_id, resource_id)
            backfill_view_access(user_id, resource_id, view_access)

        # view and discoverable actions
        if action in ["s3:ListObjects", "s3:ListObjectsV2", "s3:ListBucket"]:
            return public or allow_private_sharing or discoverable or view_access

        return public or allow_private_sharing or view_access

    # Check if edit actions are enabled via environment variable
    enable_edit_actions = os.environ.get(
        "ENABLE_EDIT_ACTIONS", "false").lower() == "true"
    if enable_edit_actions and action in EDIT_ACTIONS:
        if not is_contents_path:
            # if the prefix request is not in the contents path, do not allow edit
            return False
        if action in WRITE_ACTIONS and quota_is_exceeded(resource_id):
            return False
        try:
            edit_access = user_has_edit_access(user_id, resource_id)
        except Exception:
            edit_access = user_has_edit_access(user_id, resource_id)
            backfill_edit_access(user_id, resource_id, edit_access)
        print(f"Edit access {user_id} {resource_id} {edit_access}")
        return edit_access

    return False


class SignatureVerifyRequest(BaseModel):
    method: str
    path: str
    headers: dict
    query_params: dict
    payload_hash: str
    auth_info: dict


@router.post("/verify-signature/")
async def verify_signature(request: SignatureVerifyRequest):
    access_key = request.auth_info.get("access_key")
    if not access_key:
        return {"allow": False, "reason": "missing_access_key"}

    rows = get_user_service_account_secrets_and_id(access_key)
    candidate_secrets = []
    if rows:
        candidate_secrets = [(secret_key, int(user_id)) for secret_key, user_id in rows]
    else:
        logger.warning(f"Access key not found: {access_key}")

    for token_key, user_id in candidate_secrets:
        valid = verify_signature_v4(
            method=request.method,
            path=request.path,
            headers=request.headers,
            query_params=request.query_params,
            payload_hash=request.payload_hash,
            secret_key=token_key,
            auth_info=request.auth_info,
        )
        if valid:
            return {"allow": True, "user_id": int(user_id)}

    logger.warning(f"Invalid signature for access_key: {access_key}")
    return {"allow": False, "reason": "invalid_signature"}
