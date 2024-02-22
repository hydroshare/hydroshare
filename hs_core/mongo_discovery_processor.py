import logging
import datetime
import hs_access_control.signals

from django.conf import settings
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
    db.discovery.update_one({"resource_id": resource_id}, {"$set": {"resource_id": resource_id, "updated": datetime.datetime.now().timestamp()}}, upsert=True)


@shared_task
def remove_mongo(resource_id: str):
    db.discovery.delete_one({"resource_id": resource_id})


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
            "owner": parse_query_result(owned_resources.filter(extra_metadata__has_key="minio_resource_url")),
            "edit": parse_query_result(editable_resources.filter(extra_metadata__has_key="minio_resource_url")),
            "view": parse_query_result(viewable_resources.filter(extra_metadata__has_key="minio_resource_url")),
        },
        "username": user.username
    }

def parse_query_result(resources):
    results = []
    for resource in resources.all():
        owners = list(resource.raccess.owners.values_list("username", flat=True))
        resource_id = resource.short_id
        minio_resource_url = resource.extra_metadata["minio_resource_url"]
        results.append({"owners": owners, "resource_id": resource_id, "minio_resource_url": minio_resource_url})
    return results
