import datetime
import functools
import json
import logging

import boto3
from botocore.exceptions import ClientError
from pymongo import MongoClient
from django.conf import settings


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


# metadata keys whose string values should be converted to datetime objects
DATETIME_KEYS = {
    "datePublished",
    "dateCreated",
    "dateModified",
    "startDate",
    "endDate",
}

logger = logging.getLogger(__name__)


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


def collect_file_to_catalog(filepath: str):
    bucket_name, object_key = filepath.split('/', 1)
    response = _s3_client_for_bucket(bucket_name).get_object(Bucket=bucket_name, Key=object_key)
    parser = functools.partial(datetime_parser, object_key=object_key)
    metadata_json = json.loads(response['Body'].read(), object_hook=parser)

    if "relations" in metadata_json:
        for relation in metadata_json['relations']:
            if "name" in relation:
                if relation["name"] == "This resource has been replaced by a newer version":
                    # skip adding replaced resources to the catalog
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


def delete_file_from_catalog(filepath: str):
    _, object_key = filepath.split('/', 1)
    MongoDBClient.get_discovery_collection().delete_one({"_s3_filepath": object_key})


def find_live_metadata_file(object_key: str, exclude_bucket: str):
    """Return "{bucket}/{object_key}" for the first other zone bucket that still holds object_key, else None.

    Discovery docs are keyed by object_key alone, so when a resource moves between zone buckets
    (e.g. quota holder change) the delete of the old copy must not remove the doc of the new copy.
    Errors other than not-found are raised so callers retry rather than wrongly deleting the doc.
    """
    for zone_config in settings.RESOURCE_S3_ZONES_CONFIG.values():
        bucket_name = zone_config.get("bucket_name")
        if not bucket_name or bucket_name == exclude_bucket:
            continue
        try:
            _s3_client_for_bucket(bucket_name).head_object(Bucket=bucket_name, Key=object_key)
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                continue
            raise
        return f"{bucket_name}/{object_key}"
    return None
