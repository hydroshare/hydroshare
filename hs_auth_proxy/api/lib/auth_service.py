import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger("hs_auth_proxy")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
AUTH_SERVICE_TIMEOUT = float(os.environ.get("AUTH_SERVICE_TIMEOUT", "5.0"))


def _build_auth_payload(username: str, action: str, bucket: str, object_path: str,
                        prefixes: Optional[List[str]] = None) -> dict:
    if not action.startswith("s3:"):
        action = f"s3:{action}"

    return {
        "input": {
            "conditions": {
                "username": [username],
                "Prefix": prefixes if prefixes else []
            },
            "action": action,
            "bucket": bucket,
            "object": object_path or ""
        }
    }


def _handle_auth_response(response: httpx.Response, username: str, action: str) -> bool:
    if response.status_code != 200:
        logger.error(f"Auth service returned {response.status_code}: {response.text}")
        return False

    result = response.json()
    allowed = result.get("result", {}).get("allow", False)

    logger.debug(f"Auth check: user={username}, action={action}, allowed={allowed}")
    return allowed


async def check_authorization(
    username: str,
    action: str,
    bucket: str,
    object_path: str,
    prefixes: Optional[List[str]] = None
) -> bool:
    payload = _build_auth_payload(username, action, bucket, object_path, prefixes)
    url = f"{AUTH_SERVICE_URL}/minio/authorization/"

    try:
        async with httpx.AsyncClient(timeout=AUTH_SERVICE_TIMEOUT) as client:
            response = await client.post(url, json=payload)
            return _handle_auth_response(response, username, action)
    except httpx.TimeoutException:
        logger.error(f"Auth service timeout for user={username}, action={action}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Auth service request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error calling auth service: {e}", exc_info=True)
        return False


def check_authorization_sync(
    username: str,
    action: str,
    bucket: str,
    object_path: str,
    prefixes: Optional[List[str]] = None
) -> bool:
    payload = _build_auth_payload(username, action, bucket, object_path, prefixes)
    url = f"{AUTH_SERVICE_URL}/minio/authorization/"

    try:
        with httpx.Client(timeout=AUTH_SERVICE_TIMEOUT) as client:
            response = client.post(url, json=payload)
            return _handle_auth_response(response, username, action)
    except httpx.TimeoutException:
        logger.error(f"Auth service timeout for user={username}, action={action}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Auth service request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error calling auth service: {e}", exc_info=True)
        return False
