import logging
import hs_access_control.signals

from django.conf import settings
from hs_core.atlas_mongo import _HydroshareResourceMetadata
from hs_rest_api2.metadata import resource_metadata
from pymongo.mongo_client import MongoClient
from celery import shared_task
from hs_core.hydroshare.utils import get_resource_by_shortkey
from hs_access_control.models.privilege import PrivilegeBase, PrivilegeCodes
from django.contrib.auth.models import User
from django.dispatch import receiver


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


@receiver(hs_access_control.signals.access_changed, sender=PrivilegeBase)
def access_changed(sender, **kwargs):
    if 'users' in kwargs:
        update_mongo_user_privileges.apply_async((kwargs['users'],))
    if 'resources' in kwargs:
        update_mongo_resource_access.apply_async((kwargs['resources'],))
    logger.info("access_changed: users: {} resources: {}".format(kwargs['users'], kwargs['resources']))


@shared_task
def update_mongo_resource_access(resource_ids):
    for resource_id in resource_ids:
        resource_access_json = get_resource_access_json(resource_id)
        db.resourceaccess.update_one({"resource_id": resource_id}, {"$set": resource_access_json}, upsert=True)


def get_resource_access_json(resource_id):
    resource = get_resource_by_shortkey(resource_id)
    return {
        "resource_id": resource_id,
        "show_in_discover": resource.show_in_discover,
        "is_public": resource.raccess.public,
        "minio_resource": resource.extra_metadata.get("minio", None)  == 'cuahsi' 
    }


@shared_task
def update_mongo_user_privileges(usernames):
    for username in usernames:
        user = User.objects.get(username=username)
        user_privileges = user_resource_privileges(user)
        db.userprivileges.update_one({"username": username}, {"$set": user_privileges}, upsert=True)



def user_resource_privileges(user):
    owned_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.OWNER)
    editable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.CHANGE, via_group=True)
    viewable_resources = user.uaccess.get_resources_with_explicit_access(PrivilegeCodes.VIEW, via_group=True)
    return {
        "all": {
            "owner": list(owned_resources.values_list("short_id", flat=True).iterator()),
            "edit": list(editable_resources.values_list("short_id", flat=True).iterator()),
            "view": list(viewable_resources.values_list("short_id", flat=True).iterator()),
        },
        "minio": {
            "owner": list(owned_resources.filter(extra_metadata__minio__exact="cuahsi").values_list("short_id", flat=True).iterator()),
            "edit": list(editable_resources.filter(extra_metadata__minio__exact="cuahsi").values_list("short_id", flat=True).iterator()),
            "view": list(viewable_resources.filter(extra_metadata__minio__exact="cuahsi").values_list("short_id", flat=True).iterator()),
        },
        "username": user.username
    }