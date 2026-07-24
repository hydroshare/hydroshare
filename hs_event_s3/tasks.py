import logging
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")
django.setup()

# Django imports must come after django.setup()
from hs_core.models import BaseResource  # noqa: E402
from hs_core.hydroshare.resource import delete_resource_file  # noqa: E402
from hs_core.hydroshare_atlas_discovery_collection import (  # noqa: E402
    collect_file_to_catalog,
    delete_file_from_catalog,
)
from hs_core.views.utils import link_s3_file_to_django  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from theme.models import UserQuota  # noqa: E402

from hs_event_s3.celery_app import celery_app  # noqa: E402

logger = logging.getLogger("hs_event_s3")


def _link_s3_file_to_resource(resource, short_path: str):
    link_s3_file_to_django(resource, short_path)


@celery_app.task(
    bind=True,
    name="hs_event_s3.tasks.process_s3_event",
    max_retries=3,
    default_retry_delay=10,
)
def process_s3_event(self, action: str, bucket: str, object_path: str, username: str, user_id: int, **kwargs):
    """Process a completed S3 write or delete event from hs-s3-proxy.

    Updates Django resource metadata to reflect the S3 change.
    """
    logger.info(
        f"Processing S3 event: action={action}, bucket={bucket}, "
        f"object={object_path}, user={username} (id={user_id})"
    )

    # object_path is expected as "{resource_id}/data/contents/{relative_path}"
    parts = object_path.split("/data/contents/", 1)
    if len(parts) != 2:
        logger.warning(f"Unexpected object_path format, skipping: {object_path}")
        return

    resource_id, short_path = parts

    if username == "cuahsi":
        logger.info("Ignoring event from admin account cuahsi")
        return

    file_created = action in ("s3:PutObject", "s3:CompleteMultipartUpload")

    try:
        if file_created:
            resource = BaseResource.objects.get(short_id=resource_id)
            _link_s3_file_to_resource(resource, short_path)
            UserQuota.objects.get(user=resource.quota_holder).data_zone_value
        else:
            user = User.objects.get(pk=user_id)
            logger.info(f"Deleting file {short_path} for resource {resource_id}")
            delete_resource_file(resource_id, short_path, user)
            logger.info(f"Deleted file {short_path} for resource {resource_id}")
            resource = BaseResource.objects.get(short_id=resource_id)
            UserQuota.objects.get(user=resource.quota_holder).data_zone_value
    except Exception as exc:
        logger.error(f"Error processing S3 event for {resource_id}/{short_path}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="hs_event_s3.tasks.sync_discovery_collection",
    max_retries=3,
    default_retry_delay=10,
)
def sync_discovery_collection(self, action: str, bucket: str, object_path: str, **kwargs):
    """Sync the Atlas discovery catalog when dataset_metadata.json changes.

    Only fires for keys matching {resource_id}/.hsjsonld/dataset_metadata.json.
    """
    # object_path is {resource_id}/.hsjsonld/dataset_metadata.json
    parts = object_path.split("/", 1)
    if len(parts) != 2:
        logger.warning(f"Unexpected object_path for discovery event, skipping: {object_path}")
        return

    resource_id = parts[0]
    # Reconstruct the full MinIO key the catalog functions expect: {bucket}/{object_path}
    key = f"{bucket}/{object_path}"
    file_created = action in ("s3:PutObject", "s3:CompleteMultipartUpload")

    logger.info(
        f"Processing discovery collection event: action={action}, key={key}"
    )

    try:
        if file_created:
            res = BaseResource.objects.get(short_id=resource_id)
            if res.raccess.discoverable:
                collect_file_to_catalog(key)
            else:
                delete_file_from_catalog(key)
        else:
            delete_file_from_catalog(key)
    except Exception as exc:
        logger.error(f"Error syncing discovery catalog for {key}: {exc}", exc_info=True)
        raise self.retry(exc=exc)
