import logging

from hs_extract.celery_app import celery_app
from hsextract.utils.s3 import get_configured_zones, resolve_zone

logger = logging.getLogger("hs_extract")


@celery_app.task(name="hs_extract.tasks.extract_metadata", bind=True, max_retries=3)
def extract_metadata(self, action: str, bucket: str, object_path: str, file_size: int, zone: str, **kwargs) -> None:
    """Extract metadata for a resource file following an S3 event.

    Args:
        action: S3 action string (e.g. "s3:PutObject", "s3:DeleteObjects")
        bucket: S3 bucket (e.g. "resource")
        object_path: Path within the bucket (e.g. "{resource_id}/data/contents/file.csv")
        file_size: Size of the file in bytes (0 for delete events)
        zone: S3 zone (e.g. "us-east-1")
    """
    # Reconstruct the full key as used throughout hsextract (bucket/object_path)
    key = f"{bucket}/{object_path}"
    file_updated = not action.startswith("s3:ObjectRemoved") and not action.startswith("s3:DeleteObject")

    resolved_zone = resolve_zone(zone)
    if not resolved_zone:
        logger.error(
            "extract_metadata skipping key=%s due to empty/unknown zone '%s'. Available zones: %s",
            key,
            zone,
            ", ".join(get_configured_zones()),
        )
        return

    logger.info(
        "extract_metadata: key=%s, file_updated=%s, file_size=%s, zone=%s",
        key,
        file_updated,
        file_size,
        resolved_zone,
    )

    try:
        _handle_extract_event(key, file_size, file_updated, resolved_zone)
    except Exception as exc:
        logger.error(f"extract_metadata failed for key={key}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


def _handle_extract_event(key: str, file_size: int, file_updated: bool, zone: str) -> None:
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
        refresh_resource_metadata(bucket, resource_id, zone)
        return

    if directory == ".hsjsonld":
        return

    if directory == ".hsmetadata":
        logger.info(f"Handling .hsmetadata event for file: {key}, updated: {file_updated}, zone={zone}")
        if key == f"{bucket}/{resource_id}/.hsmetadata/user_metadata.json":
            md = BaseMetadataObject(key, file_updated, zone)
            write_resource_jsonld_metadata(md)
        elif key == f"{bucket}/{resource_id}/.hsmetadata/system_metadata.json":
            md = BaseMetadataObject(key, file_updated, zone)
            write_resource_jsonld_metadata(md)
        elif key.endswith("user_metadata.json"):
            md = determine_metadata_object_from_user_metadata(key, file_updated, zone)
            if md.content_type != ContentType.UNKNOWN:
                write_content_type_jsonld_metadata(md)
                write_resource_jsonld_metadata(md)
        else:
            logger.info(f"No event for all other files in .hsmetadata: {key}")
        return

    # Default: data/contents or other directories
    workflow_metadata_extraction(key, file_size, file_updated, zone)
