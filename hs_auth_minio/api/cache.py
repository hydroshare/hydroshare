import os

import redis

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', 6379)
REDIS_TTL = os.getenv('REDIS_TTL', 3600)

# Initialize Redis connection
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def set_cache_xx(key, value):
    redis_client.set(key, value, xx=True, ex=REDIS_TTL)


def hset_cache_xx(key, mapping):
    if redis_client.exists(key):
        redis_client.hset(key, mapping=mapping)


def is_superuser_and_id_cache(username):
    # disable cache access for now
    is_superuser, user_id = redis_client.hmget(username, ["is_superuser", "user_id"])
    if is_superuser is None:
        raise Exception
    # is_superuser is stored as a byte
    return is_superuser == b'\x00', int(user_id)


def resource_discoverability_cache(resource_id):
    # disable cache access for now
    access = redis_client.hmget(resource_id, ["access", "private_sharing"])
    if access[0] == "DISCOVERABLE":
        # public, allow_private_sharing, discoverable
        return False, access[1] == "ENABLED", True
    elif access[0] == "PUBLIC":
        return True, access[1] == "ENABLED", True
    elif access[0] == "PRIVATE":
        return False, access[1] == "ENABLED", False
    elif access[0] == None:
        raise Exception


def user_has_view_access_cache(user_id, resource_id):
    # disable cache access for now
    access = redis_client.get(f"{user_id}:{resource_id}")
    if access is None:
        raise Exception
    else:
        return access in ["VIEW", "EDIT"]


def user_has_edit_access_cache(user_id, resource_id):
    # disable cache access for now
    access = redis_client.get(f"{user_id}:{resource_id}")
    if access is None:
        raise Exception
    else:
        return access == "EDIT"


def backfill_superuser_and_id(username, is_superuser, user_id):
    redis_client.hmset(username, {"is_superuser": bytes(is_superuser), "user_id": user_id})


def backfill_resource_discoverability(resource_id, public, allow_private_sharing, discoverable):
    if public:
        access = "PUBLIC"
    elif discoverable:
        access = "DISCOVERABLE"
    else:
        access = "PRIVATE"
    redis_client.hmset(
        resource_id,
        {"access": access, "private_sharing": "ENABLED" if allow_private_sharing else "DISABLED"},
    )


def backfill_view_access(user_id, resource_id, view_access):
    redis_client.set(f"{user_id}:{resource_id}", "VIEW" if view_access else "NONE", ex=REDIS_TTL)


def backfill_edit_access(user_id, resource_id, edit_access):
    redis_client.set(f"{user_id}:{resource_id}", "EDIT" if edit_access else "VIEW", ex=REDIS_TTL)
