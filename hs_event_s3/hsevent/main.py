import redpanda_connect
import asyncio
import json
import django
import threading

django.setup()
# django imports can only happen after django is setup
from hs_core.models import BaseResource
from hs_core.hydroshare.resource import delete_resource_file
from theme.models import UserProfile
from hs_core.views.utils import link_s3_file_to_django
from hs_file_types.utils import get_logical_file_type, set_logical_file_type


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


def sync_resource(file_updated, key, resource_id, username):
    short_path = key.split(f'{resource_id}/data/contents/')[1]
    if file_updated:
        try:
            resource = BaseResource.objects.get(short_id=resource_id)
            link_s3_files_to_resource(resource, short_path)
        except Exception as e:
            print(f"Error syncing resource {resource_id}: {e}")
    else:
        try:
            print(f"Deleting file {key} for resource {resource_id}")
            # the user identity from minio is equivalent to bucket name
            user = UserProfile.objects.get(_bucket_name=username).user
            delete_resource_file(resource_id, short_path, user)
            print(f"Deleted file {key} for resource {resource_id}")
        except Exception as e:
            print(f"Error deleting file for resource {resource_id}: {e}")


@redpanda_connect.processor
def handle_minio_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    print("Received message from Redpanda print")
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_updated = json_payload['EventName'].startswith("s3:ObjectCreated")
    bucket_name = key.split('/')[0]
    resource_id = key.split('/')[1]
    username = json_payload['Records'][0]['userIdentity']['principalId']
    if username == "cuahsi":
        return
    if not key.startswith(f'{bucket_name}/{resource_id}/data/contents/'):
        # TODO: tests around this check, possibly tighten up
        print(f"Ignoring event for key {key} not in contents directory")
        return
    print(f"Processing event for resource id: {resource_id}")
    fetch_thread = threading.Thread(target=sync_resource, args=(file_updated, key, resource_id, username))
    fetch_thread.start()
    fetch_thread.join()


if __name__ == "__main__":
    asyncio.run(redpanda_connect.processor_main(handle_minio_event))
