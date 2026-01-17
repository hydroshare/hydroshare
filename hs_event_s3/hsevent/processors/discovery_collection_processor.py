import asyncio
import threading
import logging
import redpanda_connect
import json

import django
django.setup()
from hs_core.models import BaseResource
from hs_core.hydroshare_atlas_discovery_collection import collect_file_to_catalog, delete_file_from_catalog


def sync_discoverable_collection(key: str, resource_id: str, file_created: bool):
    if file_created:
        res = BaseResource.objects.get(short_id=resource_id)
        if res.raccess.discoverable:
            collect_file_to_catalog(key)
        else:
            delete_file_from_catalog(key)
    else:
        delete_file_from_catalog(key)


@redpanda_connect.processor
def discovery_collection_event(msg: redpanda_connect.Message) -> redpanda_connect.Message:
    json_payload = json.loads(msg.payload)
    key = json_payload['Key']
    file_created = json_payload['EventName'].startswith("s3:ObjectCreated")
    bucket_name = key.split('/')[0]
    resource_id = key.split('/')[1]
    if key.startswith(f'{bucket_name}/{resource_id}/.hsjsonld/'):
        fetch_thread = threading.Thread(target=sync_discoverable_collection, args=(key, resource_id, file_created))
        fetch_thread.start()
        fetch_thread.join()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(redpanda_connect.processor_main(discovery_collection_event))
