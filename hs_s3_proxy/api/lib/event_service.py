import logging
import os

import httpx

logger = logging.getLogger("hs_s3_proxy")

AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8001")
EVENT_SERVICE_TIMEOUT = float(os.environ.get("EVENT_SERVICE_TIMEOUT", "5.0"))
EVENT_SERVICE_POOL_MAX_CONNECTIONS = int(os.environ.get("EVENT_SERVICE_POOL_MAX_CONNECTIONS", "10"))
EVENT_SERVICE_POOL_MAX_KEEPALIVE_CONNECTIONS = int(
    os.environ.get("EVENT_SERVICE_POOL_MAX_KEEPALIVE_CONNECTIONS", "5")
)
EVENT_SERVICE_LIMITS = httpx.Limits(
    max_connections=EVENT_SERVICE_POOL_MAX_CONNECTIONS,
    max_keepalive_connections=EVENT_SERVICE_POOL_MAX_KEEPALIVE_CONNECTIONS,
)
EVENT_SERVICE_CLIENT = httpx.Client(
    timeout=EVENT_SERVICE_TIMEOUT,
    limits=EVENT_SERVICE_LIMITS,
)


def close_event_service_client() -> None:
    EVENT_SERVICE_CLIENT.close()


def post_s3_event(
    action: str,
    bucket: str,
    object_path: str,
    username: str,
    user_id: int,
    file_size: int = 0,
    zone: str = "",
) -> bool:
    """Notify hs-s3-auth of a completed S3 write or delete event.

    Returns True if the event was accepted, False otherwise.
    Failures are logged but never propagate — the proxy response to the client
    is already on its way when this is called.
    """
    url = f"{AUTH_SERVICE_URL}/s3/event/"
    payload = {
        "action": action,
        "bucket": bucket,
        "object_path": object_path or "",
        "username": username,
        "user_id": user_id,
        "file_size": file_size,
        "zone": zone,
    }

    try:
        response = EVENT_SERVICE_CLIENT.post(url, json=payload)
        if response.status_code not in (200, 204):
            logger.error(
                f"Event service returned {response.status_code} for {action} "
                f"on {bucket}/{object_path}: {response.text}"
            )
            return False
        logger.debug(f"S3 event posted: action={action}, bucket={bucket}, object={object_path}")
        return True
    except httpx.TimeoutException:
        logger.error(f"Event service timeout posting {action} on {bucket}/{object_path}")
        return False
    except httpx.RequestError as e:
        logger.error(f"Event service request error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error posting S3 event: {e}", exc_info=True)
        return False
