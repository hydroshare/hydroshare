import logging
import os

import httpx

logger = logging.getLogger("hs_s3_proxy")

EVENT_SERVICE_URL = os.environ.get("S3_EVENT_SERVICE_URL", "")
EVENT_SERVICE_TIMEOUT = float(os.environ.get("S3_EVENT_SERVICE_TIMEOUT", "3.0"))


def post_s3_event(
    action: str,
    bucket: str,
    object_path: str,
    username: str,
    user_id: int | None,
    file_size: int | None = None,
) -> None:
    """Best-effort event post; non-blocking for proxy success path."""
    if not EVENT_SERVICE_URL:
        return

    payload = {
        "action": action,
        "bucket": bucket,
        "object_path": object_path,
        "username": username,
        "user_id": user_id,
    }
    if file_size is not None:
        payload["file_size"] = file_size

    try:
        with httpx.Client(timeout=EVENT_SERVICE_TIMEOUT) as client:
            response = client.post(EVENT_SERVICE_URL, json=payload)
        if response.status_code >= 400:
            logger.warning(
                "Event service returned %s for action=%s bucket=%s object=%s",
                response.status_code,
                action,
                bucket,
                object_path,
            )
    except Exception as e:
        logger.warning("Failed to post S3 event: %s", e)
