from functools import lru_cache

from pydantic import BaseModel
from typing import Dict
from django.conf import settings as django_settings

class ZoneConfig(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_endpoint_url: str
    aws_s3_endpoint_url_public: str
    bucket_name: str

class SettingsConfig(BaseModel):
    resource_s3_zones_config: Dict[str, ZoneConfig] = {}
    resource_s3_default_zone: str = "hydroshare"
    
    def zone_config(self, zone_name: str) -> ZoneConfig:
        if zone_name not in self.resource_s3_zones_config:
            raise ValueError(f"Zone {zone_name} not found in configuration")
        return self.resource_s3_zones_config[zone_name]

@lru_cache(maxsize=None)
def get_default_zone_config() -> ZoneConfig:
    settings_config = get_resource_s3_zones_config()
    return get_zone_config(settings_config.resource_s3_default_zone)

@lru_cache(maxsize=None)
def get_default_zone_name() -> str:
    settings_config = get_resource_s3_zones_config()
    return settings_config.resource_s3_default_zone

@lru_cache(maxsize=None)
def get_zone_config(zone_name: str) -> ZoneConfig:
    return get_resource_s3_zones_config().zone_config(zone_name)

@lru_cache(maxsize=None)
def get_resource_s3_zones_config() -> SettingsConfig:
    return SettingsConfig(
        resource_s3_zones_config={
            zone: ZoneConfig(**config)
            for zone, config in getattr(django_settings, "RESOURCE_S3_ZONES_CONFIG", {}).items()
        },
        resource_s3_default_zone=getattr(django_settings, "RESOURCE_S3_DEFAULT_ZONE", "hydroshare")
    )