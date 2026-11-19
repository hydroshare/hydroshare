import json
import os
from functools import lru_cache

import httpx


@lru_cache(maxsize=1)
def _remote_config():
    url = os.environ["S3_ZONE_CONFIG_URL"]
    token_file = os.environ["S3_ZONE_API_TOKEN_FILE"]
    with open(token_file, encoding="utf-8") as file:
        token = file.read().strip()
    if not token:
        raise ValueError("S3 zone API token must not be empty")
    response = httpx.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    response.raise_for_status()
    config = response.json()
    if not isinstance(config, dict) or not config:
        raise ValueError("S3 zone configuration must be a non-empty object")
    return config


def load_zone_config():
    if os.environ.get("S3_ZONE_CONFIG_URL"):
        return _remote_config()
    raw = os.environ.get("S3_ZONE_CONFIG", "").strip()
    return json.loads(raw) if raw else {}
