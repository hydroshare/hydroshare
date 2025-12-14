from functools import lru_cache

from minio import Minio

from . import get_settings


@lru_cache()
def get_minio_client() -> Minio:
    return Minio(
        get_settings().minio_api_url,
        access_key=get_settings().minio_access_key,
        secret_key=get_settings().minio_secret_key,
    )
