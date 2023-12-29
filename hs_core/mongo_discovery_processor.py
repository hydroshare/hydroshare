import logging

from django.conf import settings
from hs_core.atlas_mongo import _HydroshareResourceMetadata
from hs_rest_api2.metadata import resource_metadata
from pymongo.mongo_client import MongoClient

logger = logging.getLogger(__name__)

client = MongoClient(getattr(settings, "MONGO_DISCOVERY_URL", ""), uuidRepresentation="standard")
db = client[getattr(settings, "MONGO_DISCOVERY_DATABASE", "hydroshare_beta")]


def update_mongo(res):
    res_json = resource_metadata(res)
    res_metadata = _HydroshareResourceMetadata(**res_json.dict())
    discovery_record = res_metadata.to_catalog_dataset()
    db.discovery.update_one({"url": str(res_json.url)}, {"$set": discovery_record.dict(by_alias=True)}, upsert=True)
    logger.info("updated discovery record in mongodb for " + res.short_id)

def remove_mongo(res):
    res_json = resource_metadata(res)
    db.discovery.delete_one({"url": str(res_json.url)})
    logger.info("deleted discovery record in mongodb for " + res.short_id)