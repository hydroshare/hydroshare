import logging

from api.celery_app import celery_app

logger = logging.getLogger("hs-s3-auth")


@celery_app.task(bind=True, name="api.tasks.process_s3_event", max_retries=3, default_retry_delay=10)
def process_s3_event(self, action: str, bucket: str, object_path: str, username: str, user_id: int):
    """Relay an S3 event to the hs_event_s3 worker for Django-side processing."""
    logger.info(
        f"Relaying S3 event to hs_event_s3 worker: action={action}, "
        f"bucket={bucket}, object={object_path}, user={username} (id={user_id})"
    )
    celery_app.send_task(
        "hs_event_s3.tasks.process_s3_event",
        kwargs={
            "action": action,
            "bucket": bucket,
            "object_path": object_path,
            "username": username,
            "user_id": user_id,
        },
        queue="s3_events",
    )
