import logging
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger("hs-s3-auth")


class S3Event(BaseModel):
    action: str
    bucket: str
    object_path: str
    username: str
    user_id: Optional[int] = None


@router.post("/event/", status_code=204)
async def receive_s3_event(event: S3Event):
    """Receive notification of a completed S3 write or delete from hs-s3-proxy.

    This endpoint is the integration point for downstream side-effects such as
    updating resource metadata, invalidating caches, or triggering bag jobs.
    """
    logger.info(
        f"S3 event received: action={event.action}, "
        f"bucket={event.bucket}, object={event.object_path}, "
        f"user={event.username} (id={event.user_id})"
    )
