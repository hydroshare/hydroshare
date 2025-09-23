import logging
import os
from typing import AnyStr, List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from api.cache import (
    backfill_edit_access,
    backfill_resource_discoverability,
    backfill_superuser_and_id,
    backfill_view_access,
    is_superuser_and_id_cache,
    resource_discoverability_cache,
    user_has_edit_access_cache,
    user_has_view_access_cache,
)
from api.database import is_superuser_and_id, resource_discoverability, user_has_edit_access, user_has_view_access

router = APIRouter()
logger = logging.getLogger("micro-auth")

VIEW_ACTIONS = os.environ.get(
    "MINIO_VIEW_ACTIONS",
    "s3:GetObject,s3:ListObjects,s3:ListObjectsV2,s3:ListBucket,s3:GetObjectRetention,s3:GetObjectLegalHold",
).split(",")
EDIT_ACTIONS = os.environ.get(
    "MINIO_EDIT_ACTIONS", "s3:PutObject,s3:DeleteObject,s3:DeleteObjects,s3:UploadPart,s3:PutObjectLegalHold"
).split(",")


class AllowBaseModel(BaseModel, extra='allow'):
    pass


class Conditions(AllowBaseModel):
    preferred_username: Optional[List[AnyStr]] = []
    username: Optional[List[AnyStr]] = []
    Prefix: Optional[List[AnyStr]] = []
    prefix: Optional[List[AnyStr]] = []

    @property
    def users(self):
        if self.preferred_username:
            return self.preferred_username
        else:
            return self.username

    @property
    def user(self):
        users = self.users
        if len(users) != 1:
            logger.warning(f"Exactly one user must be specified {users}")
            raise ValueError("Exactly one user must be specified")
        return self.users[0]

    @property
    def prefixes(self):
        if self.Prefix:
            return [prefix for prefix in self.Prefix if prefix]
        elif self.prefix:
            return [prefix for prefix in self.prefix if prefix]
        else:
            return []


class Input(AllowBaseModel):
    conditions: Conditions
    # https://min.io/docs/minio/linux/administration/identity-access-management/policy-based-access-control.html
    action: AnyStr
    bucket: AnyStr
    object: AnyStr


class AuthRequest(AllowBaseModel):
    input: Input


@router.post("/authorization/")
async def hs_s3_authorization_check(auth_request: AuthRequest):

    username = auth_request.input.conditions.user
    bucket = auth_request.input.bucket
    action = auth_request.input.action

    if username == "cuahsi" or username == "minioadmin":
        # allow cuahsi admin account always
        return {"result": {"allow": True}}

    if auth_request.input.action in ["s3:GetBucketLocation", "s3:GetBucketObjectLockConfiguration"]:
        # This is needed by mc to list buckets and does not contain a prefix
        return {"result": {"allow": True}}

    try:
        user_is_superuser, user_id = is_superuser_and_id(username)
    except:
        user_is_superuser, user_id = is_superuser_and_id(username)
        logger.warning(f"Backfilling cache: {username}:(is_superuser:{user_is_superuser},user_id:{user_id})")
        backfill_superuser_and_id(username, user_is_superuser, user_id)
    if user_is_superuser:
        return {"result": {"allow": True}}

    # users access the objects in these buckets through presigned urls, admins are approved above
    if bucket in ["zips", "tmp", "bags"]:
        return {"result": {"allow": False}}

    # prefixes are paths to (folders/set of) objects in the bucket
    prefixes = auth_request.input.conditions.prefixes
    if not prefixes:
        if auth_request.input.object:
            # if there is an object but no prefix, it is a file in the root of the bucket
            prefixes = [auth_request.input.object]
        else:
            return {"result": {"allow": False}}

    # extracted metadata has a prefix of "md/resource_id" and should be view only
    resource_ids_and_is_md_path = [
        (prefix.split("/")[0], False) if prefix.split("/")[0] != "md" else (prefix.split("/")[1], True)
        for prefix in prefixes
    ]
    # check the user and each resource against the action
    for resource_id, is_md_path in resource_ids_and_is_md_path:
        if not _check_user_authorization(user_id, resource_id, action, is_md_path):
            return {"result": {"allow": False}}
    if resource_ids_and_is_md_path:
        return {"result": {"allow": True}}

    return {"result": {"allow": False}}


def _check_user_authorization(user_id, resource_id, action, is_md_path):
    # Break this down into just view and edit for now.
    # We may need to make owners distinct from edit at some point

    # List of actions https://docs.aws.amazon.com/AmazonS3/latest/API/API_Operations.html

    # view actions
    if action in VIEW_ACTIONS:
        try:
            public, allow_private_sharing, discoverable = resource_discoverability(resource_id)
        except:
            public, allow_private_sharing, discoverable = resource_discoverability(resource_id)
            backfill_resource_discoverability(resource_id, public, allow_private_sharing, discoverable)

        try:
            view_access = user_has_view_access(user_id, resource_id)
        except:
            view_access = user_has_view_access(user_id, resource_id)
            backfill_view_access(user_id, resource_id, view_access)

        if action in ["s3:GetObject", "s3:GetObjectRetention", "s3:GetObjectLegalHold"]:
            return public or allow_private_sharing or view_access
        # view and discoverable actions
        if action in ["s3:ListObjects", "s3:ListObjectsV2", "s3:ListBucket"]:
            return public or allow_private_sharing or discoverable or view_access

    # Check if edit actions are enabled via environment variable
    enable_edit_actions = os.environ.get("ENABLE_EDIT_ACTIONS", "false").lower() == "true"
    if enable_edit_actions and action in EDIT_ACTIONS:
        if is_md_path:
            # if the prefix request is a metadata path, we do not allow edit access
            return False
        try:
            edit_access = user_has_edit_access(user_id, resource_id)
        except:
            edit_access = user_has_edit_access(user_id, resource_id)
            backfill_edit_access(user_id, resource_id, edit_access)
        print(f"Edit access {user_id} {resource_id} {edit_access}")
        return edit_access

    return False
