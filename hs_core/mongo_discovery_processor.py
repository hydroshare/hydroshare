import logging

from django.conf import settings
from hs_core.atlas_mongo import _HydroshareResourceMetadata
from hs_rest_api2.metadata import resource_metadata
from pymongo.mongo_client import MongoClient
from celery import shared_task
from hs_core.hydroshare.utils import get_resource_by_shortkey


logger = logging.getLogger(__name__)

client = MongoClient(getattr(settings, "MONGO_DISCOVERY_URL", ""), uuidRepresentation="standard")
db = client[getattr(settings, "MONGO_DISCOVERY_DATABASE", "hydroshare_beta")]


@shared_task
def update_mongo(resource_id: str):
    db.discovery.update_one({"resource_id": resource_id}, {"$set": {"resource_id": resource_id}}, upsert=True)

@shared_task
def remove_mongo(resource_id: str):
    db.discover_ids_delete_one({"resource_id": resource_id})