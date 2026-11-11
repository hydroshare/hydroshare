import datetime
import functools
import json
import logging
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from pymongo import MongoClient
from django.conf import settings
from hsmodels.schemas.enums import RelationType


@functools.lru_cache(maxsize=None)
def _make_s3_client(zone=None):
    zone_config = settings.RESOURCE_S3_ZONES_CONFIG.get(
        zone or settings.RESOURCE_S3_DEFAULT_ZONE, {}
    )
    kwargs = {}
    if zone_config.get("aws_s3_endpoint_url"):
        kwargs["endpoint_url"] = zone_config["aws_s3_endpoint_url"]
    if zone_config.get("aws_access_key_id"):
        kwargs["aws_access_key_id"] = zone_config["aws_access_key_id"]
    if zone_config.get("aws_secret_access_key"):
        kwargs["aws_secret_access_key"] = zone_config["aws_secret_access_key"]
    return boto3.client('s3', **kwargs)


s3 = _make_s3_client()


def _s3_client_for_bucket(bucket_name: str):
    """Return an S3 client using the credentials/endpoint of the zone that owns bucket_name.

    Zones may live on different endpoints/projects, so a non-default zone bucket must not be
    read with the default-zone client. Unknown buckets fall back to the default-zone client.
    """
    for zone, zone_config in settings.RESOURCE_S3_ZONES_CONFIG.items():
        if zone_config.get("bucket_name") == bucket_name and zone != settings.RESOURCE_S3_DEFAULT_ZONE:
            return _make_s3_client(zone)
    return s3


# S3 object key template for a resource's dataset metadata; fill with str.format(resource_id=...)
METADATA_OBJECT_KEY_TEMPLATE = "{resource_id}/.hsjsonld/dataset_metadata.json"

# metadata keys whose string values should be converted to datetime objects
DATETIME_KEYS = {
    "datePublished",
    "dateCreated",
    "dateModified",
    "startDate",
    "endDate",
}

logger = logging.getLogger(__name__)

# relation names and sharing statuses used to decide which versions belong in the catalog
REPLACED_BY_RELATION_NAME = RelationType.isReplacedBy.value
REPLACES_RELATION_NAME = RelationType.isVersionOf.value
VISIBLE_SHARING_STATUSES = {"Public", "Published", "Discoverable"}


class MongoDBClient:
    """Provides connection to MongoDB collections."""

    _collection = None

    @classmethod
    def get_discovery_collection(cls):
        if cls._collection is None:
            cls._collection = MongoClient(settings.ATLAS_CONNECTION_URL)[settings.ATLAS_DB_NAME]["discovery"]
        return cls._collection


def datetime_parser(dct, object_key=None):
    for k, v in dct.items():
        if k in DATETIME_KEYS and isinstance(v, str):
            try:
                dct[k] = datetime.datetime.fromisoformat(v)
            except ValueError:
                logger.warning(
                    f"Could not parse {k} value {v!r} as datetime in {object_key}; leaving as string"
                )
    return dct


def _resource_id_from_url(url):
    """Return the resource id from a HydroShare resource URL such as https://host/resource/<id>/."""
    parts = [part for part in urlparse(str(url or "")).path.split('/') if part]
    if len(parts) >= 2 and parts[-2] == 'resource':
        return parts[-1]
    return None


def _get_related_resources_by_name(metadata_json: dict, relation_name: str) -> list:
    """Return the resource ids referenced by relations with the given name."""
    resource_ids = []
    for relation in metadata_json.get('relation', []):
        if relation.get('name') != relation_name:
            continue
        resource_id = _resource_id_from_url(relation.get('url'))
        if resource_id:
            resource_ids.append(resource_id)
        else:
            logger.warning(f"Could not parse resource id from relation {relation!r}")
    return resource_ids


def _is_visible_status(metadata_json: dict) -> bool:
    """True when the resource is public, published, or discoverable."""
    status = metadata_json.get('creativeWorkStatus')
    return isinstance(status, dict) and status.get('name') in VISIBLE_SHARING_STATUSES


def _next_version_id(metadata_json: dict) -> str | None:
    """Return the id of the next version (the resource that replaces this one), or None."""
    next_ids = _get_related_resources_by_name(metadata_json, REPLACED_BY_RELATION_NAME)
    if len(next_ids) > 1:
        logger.warning(f"Expected one next version, found {len(next_ids)}: {next_ids}")
    return next_ids[0] if next_ids else None


def _previous_version_id(metadata_json: dict) -> str | None:
    """Return the id of the previous version (the resource this one replaces), or None."""
    previous_ids = _get_related_resources_by_name(metadata_json, REPLACES_RELATION_NAME)
    if len(previous_ids) > 1:
        logger.warning(f"Expected one previous version, found {len(previous_ids)}: {previous_ids}")
    return previous_ids[0] if previous_ids else None


def _load_metadata(bucket_name: str, object_key: str) -> dict:
    """Read dataset metadata JSON from S3, converting date fields to datetimes. Raises on failure."""
    response = _s3_client_for_bucket(bucket_name).get_object(Bucket=bucket_name, Key=object_key)
    parser = functools.partial(datetime_parser, object_key=object_key)
    return json.loads(response['Body'].read(), object_hook=parser)


def _load_resource_metadata(bucket_name: str, resource_id: str) -> dict | None:
    """Read a resource's metadata from S3, or return None if it doesn't exists."""
    object_key = METADATA_OBJECT_KEY_TEMPLATE.format(resource_id=resource_id)
    try:
        return _load_metadata(bucket_name, object_key)
    except ClientError as error:
        if error.response.get('Error', {}).get('Code') != 'NoSuchKey':
            raise
        logger.warning(f"Metadata for version {resource_id} is missing from {bucket_name}, ignoring it")
        return None


def _load_adjacent_version(bucket_name: str, version_id: str | None) -> list:
    """Return [(id, metadata)] for an adjacent version, or [] if there is none or its metadata is missing."""
    if version_id is None:
        return []
    metadata = _load_resource_metadata(bucket_name, version_id)
    return [] if metadata is None else [(version_id, metadata)]


def _adjacent_versions(bucket_name: str, resource_id: str, metadata_json: dict) -> list:
    """Return (id, metadata) pairs for this resource and its previous and next versions, oldest first."""
    return (
        _load_adjacent_version(bucket_name, _previous_version_id(metadata_json))
        + [(resource_id, metadata_json)]
        + _load_adjacent_version(bucket_name, _next_version_id(metadata_json))
    )


def collect_file_to_catalog(filepath: str):
    """Index one dataset metadata file in the discovery collection, without considering other versions."""
    logger.info(f"Adding file to Discovery: {filepath}")
    bucket_name, object_key = filepath.split('/', 1)
    _index_metadata(object_key, _load_metadata(bucket_name, object_key))


def _index_metadata(object_key: str, metadata_json: dict):
    resource_id = object_key.split('/', 1)[0]
    metadata_json['_s3_filepath'] = object_key
    metadata_json['first_creator'] = (
        metadata_json['creator'][0]
        if 'creator' in metadata_json and metadata_json['creator']
        else None
    )
    if metadata_json['first_creator']:
        if 'name' in metadata_json['first_creator']:
            if metadata_json['first_creator']['name']:
                # encountered some names with leading whitespace which causes sorting issues
                metadata_json['first_creator']['name'] = metadata_json['first_creator']['name'].strip()

    # DISABLED FOR NOW: reading content types for discovery from db exported to user metadata
    # content_types = []
    # if "hasPart" in metadata_json:
    #     for part in metadata_json['hasPart']:
    #         part_key = '/'.join(urlparse(part['url']).path.split('/')[2:])
    #         s3_response = s3.get_object(Bucket=bucket_name, Key=part_key)
    #         s3_object_body = s3_response.get('Body')
    #         content = s3_object_body.read()
    #         json_dict = json.loads(content)
    #         content_types.append(json_dict.get('additionalType'))
    #     metadata_json['content_types'] = list(set(content_types))

    MongoDBClient.get_discovery_collection().find_one_and_replace(
        {
            "_s3_filepath": metadata_json["_s3_filepath"]
        },
        metadata_json,
        upsert=True
    )
    logger.info(f"Indexed resource {resource_id} in discovery collection")


def delete_file_from_catalog(filepath: str):
    logger.info(f"delete_file_from_catalog called for {filepath}")
    _, object_key = filepath.split('/', 1)
    result = MongoDBClient.get_discovery_collection().delete_one({"_s3_filepath": object_key})
    logger.info(f"delete_file_from_catalog removed {result.deleted_count} document(s) for {object_key}")


def sync_resource_in_catalog(filepath: str, discoverable: bool):
    """Bring the Discovery collection up to date with a resource whose metadata changed.

    Of the resource and its adjacent versions, only the newest visible one belongs in the collection.
    The changed resource's visibility is the given flag; other versions use the status in their metadata.
    """
    bucket_name, object_key = filepath.split('/', 1)
    resource_id = object_key.split('/', 1)[0]
    metadata_json = _load_metadata(bucket_name, object_key)
    versions = _adjacent_versions(bucket_name, resource_id, metadata_json)

    catalog_version_id = None
    for version_id, metadata in versions:
        if version_id == resource_id:
            visible = discoverable
        else:
            visible = _is_visible_status(metadata)
        if visible:
            catalog_version_id = version_id

    for version_id, metadata in versions:
        version_key = METADATA_OBJECT_KEY_TEMPLATE.format(resource_id=version_id)
        if version_id == catalog_version_id:
            _index_metadata(version_key, metadata)
        else:
            delete_file_from_catalog(f"{bucket_name}/{version_key}")
