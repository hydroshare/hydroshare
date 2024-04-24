import json

from django.conf import settings
from google.auth import jwt
from google.cloud import pubsub_v1

publish_discoverable = getattr(settings, "PUBLISH_DISCOVERABLE", True)

if publish_discoverable:
    audience = "https://pubsub.googleapis.com/google.pubsub.v1.Publisher"
    credentials = jwt.Credentials.from_service_account_file('service-account-pubsub.json', audience=audience)
    credentials_pub = credentials.with_claims(audience=audience)
    publisher = pubsub_v1.PublisherClient(credentials=credentials_pub)

    topic_name = 'projects/{project_id}/topics/{topic}'.format(
        project_id="apps-320517", topic='discovery_ids')

def pub_update(resource_id: str, removed: bool = False):
    if publish_discoverable:
        publisher.publish(topic_name, json.dumps({"resource_id": resource_id, "removed": removed}).encode("utf-8"))
