from django.conf import settings
from pymongo.mongo_client import MongoClient
from celery import shared_task
from datetime import datetime

discovery_url = getattr(settings, "MONGO_DISCOVERY_URL", None)
db = None
if discovery_url:
    client = MongoClient(discovery_url, uuidRepresentation="standard")
    db = client[getattr(settings, "MONGO_DISCOVERY_DATABASE", "hydroshare_beta")]


@shared_task
def update_mongo(resource_id: str):
    if db:
        db.discovery_ids.update_one({"resource_id": resource_id}, {"$set": {"resource_id": resource_id,
                                                                        "update_time": datetime.now()}}, upsert=True)


@shared_task
def remove_mongo(resource_id: str):
    if db:
        db.discover_ids.delete_one({"resource_id": resource_id})
