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
    res = get_resource_by_shortkey(resource_id)
    res_json = resource_metadata(res)
    res_metadata = _HydroshareResourceMetadata(**res_json.dict())
    discovery_record = res_metadata.to_catalog_dataset()
    db.discovery.update_one({"url": str(res_json.url)}, {"$set": discovery_record.dict(by_alias=True)}, upsert=True)

@shared_task
def remove_mongo(resource_id: str):
    res = get_resource_by_shortkey(resource_id)
    res_json = resource_metadata(res)
    db.discovery.delete_one({"url": str(res_json.url)})