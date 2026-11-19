import logging
import os

from celery import Celery
from kombu.exceptions import OperationalError

logger = logging.getLogger("hs_s3_proxy")

BROKER_URL = os.getenv("CELERY_BROKER_URL")
DOWNLOAD_BROKER_SOCKET_TIMEOUT = 0.3
celery_app = Celery(
    "hs_s3_proxy",
    broker=BROKER_URL,
    task_serializer="json",
    broker_transport_options={
        "socket_connect_timeout": DOWNLOAD_BROKER_SOCKET_TIMEOUT,
        "socket_timeout": DOWNLOAD_BROKER_SOCKET_TIMEOUT,
        "retry_on_timeout": False,
    },
)


def publish_s3_download(bucket: str, object_path: str, username: str, user_id: int) -> None:
    """Queue download tracking after the response, using Starlette's thread pool."""
    if not BROKER_URL:
        logger.warning("S3 download tracking skipped: CELERY_BROKER_URL is not configured")
        return

    try:
        celery_app.send_task(
            "hs_event_s3.tasks.record_s3_download",
            kwargs={
                "action": "s3:GetObject",
                "bucket": bucket,
                "object_path": object_path,
                "username": username,
                "user_id": user_id,
            },
            queue="s3_events",
            ignore_result=True,
            retry=False,
        )
    except OperationalError as exc:
        logger.warning(
            "Could not publish S3 download tracking for %s/%s (%s)",
            bucket, object_path, type(exc).__name__,
        )
