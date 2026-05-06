import logging
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hydroshare.settings")
django.setup()

# Django imports must come after django.setup()
from hs_core.models import BaseResource  # noqa: E402
from hs_core.hydroshare.resource import delete_resource_file  # noqa: E402
from hs_core.views.utils import link_s3_file_to_django  # noqa: E402
from hs_file_types.utils import get_logical_file_type, set_logical_file_type  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from theme.models import UserQuota  # noqa: E402

from hs_event_s3.celery_app import celery_app  # noqa: E402

logger = logging.getLogger("hs_event_s3")


def _link_s3_file_to_resource(resource, short_path: str):
    res_file = link_s3_file_to_django(resource, short_path)
    if resource.resource_type == "CompositeResource":
        file_type = get_logical_file_type(res=resource, file_id=res_file.pk, fail_feedback=False)
        if not res_file.has_logical_file and file_type is not None:
            set_logical_file_type(res=resource, user=None, file_id=res_file.pk, fail_feedback=False)


@celery_app.task(
    bind=True,
    name="hs_event_s3.tasks.process_s3_event",
    max_retries=3,
    default_retry_delay=10,
)
def process_s3_event(self, action: str, bucket: str, object_path: str, username: str, user_id: int):
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
