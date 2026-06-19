import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from api.celery_app import celery_app

router = APIRouter()
logger = logging.getLogger("hs-s3-auth")


class S3Event(BaseModel):
    action: str
    bucket: str
    object_path: str
    username: str
    user_id: Optional[int] = None
    file_size: int = 0
    zone: str


@router.post("/event/", status_code=204)
async def receive_s3_event(event: S3Event):
    """Receive notification of a completed S3 write or delete from hs-s3-proxy.

    Dispatches directly to the hs_event_s3 Celery worker for Django-side
    processing (metadata updates, cache invalidation, bag/zip jobs, etc.).
    """
    logger.info(
        f"S3 event received: action={event.action}, "
        f"bucket={event.bucket}, object={event.object_path}, "
        f"user={event.username} (id={event.user_id})"
    )
    celery_app.send_task(
        "hs_event_s3.tasks.process_s3_event",
        kwargs={
            "action": event.action,
            "bucket": event.bucket,
            "object_path": event.object_path,
            "username": event.username,
            "user_id": event.user_id,
            "zone": event.zone
        },
        queue="s3_events",
    )

    # Dispatch discovery catalog sync when the jsonld metadata file changes
    if event.object_path.endswith("/.hsjsonld/dataset_metadata.json"):
        celery_app.send_task(
            "hs_event_s3.tasks.sync_discovery_collection",
            kwargs={
                "action": event.action,
                "bucket": event.bucket,
                "object_path": event.object_path,
                "zone": event.zone
            },
            queue="s3_events",
        )

    # Dispatch metadata extraction for data file events
    _path_lower = event.object_path.lower()
    if not _path_lower.endswith(".hsjsonld/dataset_metadata.json"):
        celery_app.send_task(
            "hs_extract.tasks.extract_metadata",
            kwargs={
                "action": event.action,
                "bucket": event.bucket,
                "object_path": event.object_path,
                "file_size": event.file_size,
                "zone": event.zone
            },
            queue="extract",
        )
