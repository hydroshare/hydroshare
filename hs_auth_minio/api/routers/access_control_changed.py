import logging
from typing import List

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

import api.cache as cache

router = APIRouter()
logger = logging.getLogger("micro-auth")


class UserAccess(BaseModel):
    id: str
    access: str


class ResourceAccess(BaseModel):
    id: str
    user_access: List[UserAccess]
    public: bool
    discoverable: bool
    allow_private_sharing: bool
    bucket_name: str


class AccessControlChanged(BaseModel):
    resources: List[ResourceAccess]


@router.post("/hook/")
async def set_auth(access_control_changed: AccessControlChanged, response: Response):
    try:
        for resource in access_control_changed.resources:
            resource_id = resource.id
            for user_access in resource.user_access:
                user_id = user_access.id
                access = user_access.access
                cache.set_cache_xx(f"{user_id}:{resource_id}", access)

            if resource.public:
                resource_access = "PUBLIC"
            elif resource.discoverable:
                resource_access = "DISCOVERABLE"
            else:
                resource_access = "PRIVATE"
            cache.hset_cache_xx(
                resource_id,
                {
                    "access": resource_access,
                    "private_sharing": "ENABLED" if resource.allow_private_sharing else "DISABLED",
                    "bucket_name": resource.bucket_name,
                },
            )
            response.status_code = status.HTTP_204_NO_CONTENT

    except Exception as e:
        logger.exception("Error processing request")
        raise
