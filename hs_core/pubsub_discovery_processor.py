import json

from django.conf import settings
from google.auth import jwt
from google.cloud import pubsub_v1
from celery import shared_task
from concurrent import futures

publish_discoverable = getattr(settings, "PUBLISH_DISCOVERABLE", False)

if publish_discoverable:
    audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    credentials = jwt.Credentials.from_service_account_file('service-account-pubsub.json', audience=audience)
    credentials_pub = credentials.with_claims(audience=audience)
    publisher = pubsub_v1.PublisherClient(credentials=credentials_pub)

    topic_name = 'projects/{project_id}/topics/{topic}'.format(
        project_id="apps-320517", topic='discovery_ids')

@shared_task
def pub_update(resource_id: str, removed: bool = False):
    if publish_discoverable:
        future = publisher.publish(topic_name, json.dumps({"resource_id": resource_id, "removed": removed}))
        future.result()
