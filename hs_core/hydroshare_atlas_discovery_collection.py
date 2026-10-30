import datetime
import functools
import json
import logging
from urllib.parse import urlparse

import boto3
from pymongo import MongoClient
from django.conf import settings
from hsmodels.schemas.enums import RelationType


def _make_s3_client():
    zone_config = settings.RESOURCE_S3_ZONES_CONFIG.get(
        settings.RESOURCE_S3_DEFAULT_ZONE, {}
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


def _get_resource_from_discovery(resource_id: str, projection: dict | None = None) -> dict | None:
    """Return the discovery document for a resource id, or None if it is not in the collection."""
    if projection is None:
        projection = {"_id": 1}
    return MongoDBClient.get_discovery_collection().find_one(
        {"_s3_filepath": METADATA_OBJECT_KEY_TEMPLATE.format(resource_id=resource_id)},
        projection,
    )


def _next_version_visible_in_catalog(next_id: str) -> bool:
    """True when the next version is in the discovery collection and public, published, or discoverable."""
    doc = _get_resource_from_discovery(next_id, {"creativeWorkStatus": 1})
    return doc is not None and _is_visible_status(doc)


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
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    parser = functools.partial(datetime_parser, object_key=object_key)
    return json.loads(response['Body'].read(), object_hook=parser)


def collect_file_to_catalog(filepath: str):
    logger.info(f"Adding file to Discovery: {filepath}")
    bucket_name, object_key = filepath.split('/', 1)
    resource_id = object_key.split('/', 1)[0]
    metadata_json = _load_metadata(bucket_name, object_key)

    # A replaced resource is deleted if its next version is in the collection and visible
    next_version_id = _next_version_id(metadata_json)
    if next_version_id is not None:
        if _next_version_visible_in_catalog(next_version_id):
            logger.info(
                f"Deleting {resource_id} from Discovery: next version {next_version_id} is in the collection "
                "and public, published, or discoverable"
            )
            # Remove this version from the collection if its next version is visible
            delete_file_from_catalog(f"{bucket_name}/{object_key}")
            return

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

    # A public, published, or discoverable resource removes the version it replaces
    previous_version_id = _previous_version_id(metadata_json)
    if previous_version_id is None or not _is_visible_status(metadata_json):
        return
    if _get_resource_from_discovery(previous_version_id):
        previous_key = METADATA_OBJECT_KEY_TEMPLATE.format(resource_id=previous_version_id)
        logger.info(f"{resource_id} is visible and replaces {previous_version_id}; removing previous version from collection")
        delete_file_from_catalog(f"{bucket_name}/{previous_key}")


def delete_file_from_catalog(filepath: str):
    logger.info(f"delete_file_from_catalog called for {filepath}")
    _, object_key = filepath.split('/', 1)
    result = MongoDBClient.get_discovery_collection().delete_one({"_s3_filepath": object_key})
    logger.info(f"delete_file_from_catalog removed {result.deleted_count} document(s) for {object_key}")


def handle_s3_mutation(action: str, bucket: str, object_path: str, status_code: int):
    """Sync Atlas discovery docs when dataset metadata jsonld is written/deleted."""
    if status_code not in (200, 204):
        return
    if not object_path.endswith('/.hsjsonld/dataset_metadata.json'):
        return

    key = f"{bucket}/{object_path}"
    if action in ("s3:PutObject", "s3:CompleteMultipartUpload"):
        collect_file_to_catalog(key)
    elif action in ("s3:DeleteObject", "s3:DeleteObjects"):
        delete_file_from_catalog(key)
