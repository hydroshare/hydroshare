import redpanda_connect
import asyncio
import json
import django
import threading
import logging

from django.core.exceptions import ObjectDoesNotExist
from json import JSONDecodeError

django.setup()
# django imports can only happen after django is setup
from hs_core.models import BaseResource
from hs_core.hydroshare.resource import delete_resource_file
from theme.models import UserProfile
from hs_core.views.utils import link_s3_file_to_django
from hs_file_types.utils import get_logical_file_type, set_logical_file_type

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [hs_event_s3] %(message)s",
)


def link_s3_files_to_resource(resource, fullpath):
    try:
        res_file = link_s3_file_to_django(resource, fullpath)
        # Create required logical files as necessary
        if resource.resource_type == "CompositeResource":
            file_type = get_logical_file_type(res=resource, file_id=res_file.pk, fail_feedback=False)
            if not res_file.has_logical_file and file_type is not None:
                set_logical_file_type(res=resource, user=None, file_id=res_file.pk, fail_feedback=False)
    except Exception as e:
        print(f"Error syncing resource {resource.short_id}: {e}")


def sync_resource(file_created, key, resource_id, username):
    short_path = key.split(f"{resource_id}/data/contents/")[1]
    if file_created:
        try:
            resource = BaseResource.objects.get(short_id=resource_id)
            link_s3_files_to_resource(resource, short_path)
        except Exception as e:
            print(f"Error syncing resource {resource_id}: {e}")
    else:
        # assume file deleted, only tracking put,delete events in kafka
        try:
            print(f"Deleting file {key} for resource {resource_id}")
            # the user identity from minio is equivalent to bucket name
            user = UserProfile.objects.get(_bucket_name=username).user
            delete_resource_file(resource_id, short_path, user)
            print(f"Deleted file {key} for resource {resource_id}")
        except Exception as e:
            print(f"Error deleting file for resource {resource_id}: {e}")

def _run_with_error_capture(target, *args, **kwargs):
    """Run a callable inside a thread and return an exception if it occurs."""
    captured_exception = {}

    def _runner():
        try:
            target(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            captured_exception["exception"] = exc
            logger.exception("Error while processing event: %s", exc)

    fetch_thread = threading.Thread(target=_runner)
    fetch_thread.start()
    fetch_thread.join()

    if "exception" in captured_exception:
        raise captured_exception["exception"]


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    logger.info("Received message from Redpanda")
    try:
        payload_raw = msg.payload.decode() if isinstance(msg.payload, (bytes, bytearray)) else msg.payload
        json_payload = json.loads(payload_raw)
    except (JSONDecodeError, UnicodeDecodeError):
        logger.exception("Failed to decode payload from Redpanda: %s", msg.payload)
        # Surface the error to the pipeline catch block
        raise

    key = json_payload.get("Key")
    event_name = json_payload.get("EventName", "")
    bucket_name = key.split("/")[0] if key else ""
    resource_id = key.split("/")[1] if key else ""
    username = json_payload.get("Records", [{}])[0].get("userIdentity", {}).get("principalId")

    if not key or not resource_id:
        logger.error("Missing key or resource id in event payload: %s", json_payload)
        raise ValueError("Incomplete event payload - key or resource id missing")

    if username == "cuahsi":
        logger.info("Ignoring system event for resource %s (cuahsi user)", resource_id)
        return msg

    contents_prefix = f"{bucket_name}/{resource_id}/data/contents/"
    if not key.startswith(contents_prefix):
        # TODO: tests around this check, possibly tighten up
        logger.info("Ignoring event for key %s not in contents directory", key)
        return msg

    file_created = event_name.startswith("s3:ObjectCreated")
    logger.info(
        "Processing event for resource id: %s | created=%s | key=%s",
        resource_id,
        file_created,
        key,
    )

    try:
        _run_with_error_capture(sync_resource, file_created, key, resource_id, username)
    except ObjectDoesNotExist as exc:
        logger.exception(
            "Object not found while processing event (resource_id=%s, key=%s): %s",
            resource_id,
            key,
            exc,
        )
        raise
    except Exception:
        # Let pipeline catch/log handle the rest
        logger.exception(
            "Unhandled error while processing event (resource_id=%s, key=%s)",
            resource_id,
            key,
        )
        raise

    return msg


if __name__ == "__main__":
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
