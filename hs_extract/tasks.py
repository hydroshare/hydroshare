import logging

from hs_extract.celery_app import celery_app

logger = logging.getLogger("hs_extract")


@celery_app.task(name="hs_extract.tasks.extract_metadata", bind=True, max_retries=3)
def extract_metadata(self, action: str, bucket: str, object_path: str, file_size: int = 0):
    """Extract metadata for a resource file following an S3 event.

    Args:
        action: S3 action string (e.g. "s3:PutObject", "s3:DeleteObjects")
        bucket: S3 bucket (e.g. "resource")
        object_path: Path within the bucket (e.g. "{resource_id}/data/contents/file.csv")
        file_size: Size of the file in bytes (0 if unknown)
    """
    # Reconstruct the full key as used throughout hsextract (bucket/object_path)
    key = f"{bucket}/{object_path}"
    file_updated = not action.startswith("s3:ObjectRemoved") and not action.startswith("s3:DeleteObject")

    logger.info(f"extract_metadata: key={key}, file_updated={file_updated}, file_size={file_size}")

    try:
        _handle_extract_event(key, file_size, file_updated)
    except Exception as exc:
        logger.error(f"extract_metadata failed for key={key}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def _handle_extract_event(key: str, file_size: int, file_updated: bool) -> None:
    """Core extraction logic ported from hsextract/main.py handle_minio_event."""
    # Late imports so Celery can start without the full environment if needed
    from hsextract.content_types.models import ContentType
    from hsextract.content_types import (
        BaseMetadataObject,
        determine_metadata_object_from_user_metadata,
    )
    from hs_extract.hsextract.main import (
        refresh_resource_metadata,
        workflow_metadata_extraction,
        write_content_type_jsonld_metadata,
        write_resource_jsonld_metadata,
    )

    parts = key.split("/")
    if len(parts) < 3:
        logger.warning(f"Unexpected key format, skipping: {key}")
        return

    bucket = parts[0]
    resource_id = parts[1]
    directory = parts[2]

    if directory == ".hsrefresh":
        refresh_resource_metadata(bucket, resource_id)
        return

    if directory == ".hsjsonld":
        return

    if directory == ".hsmetadata":
        logger.info(f"Handling .hsmetadata event for file: {key}, updated: {file_updated}")
        if key == f"{bucket}/{resource_id}/.hsmetadata/user_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key == f"{bucket}/{resource_id}/.hsmetadata/system_metadata.json":
            md = BaseMetadataObject(key, file_updated)
            write_resource_jsonld_metadata(md)
        elif key.endswith("user_metadata.json"):
            md = determine_metadata_object_from_user_metadata(key, file_updated)
            if md.content_type != ContentType.UNKNOWN:
                write_content_type_jsonld_metadata(md)
                write_resource_jsonld_metadata(md)
        else:
            logger.info(f"No event for all other files in .hsmetadata: {key}")
        return

    # Default: data/contents or other directories
    workflow_metadata_extraction(key, file_size, file_updated)
