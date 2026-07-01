from __future__ import annotations
import ast
import json
import logging
import mimetypes
import os
from tempfile import SpooledTemporaryFile
from typing import Iterator, Protocol, TYPE_CHECKING

import boto3
import requests
from hs_cloudnative_schemas.schema.base import HasPart, MediaObject
if TYPE_CHECKING:
    from hsextract.content_types.models import ContentType


class SupportsFileManifest(Protocol):
    @property
    def is_content_file(self) -> bool:
        ...

    content_type: ContentType
    resource_contents_path: str
    resource_associated_media_jsonld_path: str
    content_type_contents_path: str
    content_type_associated_media_jsonld_path: str


JSON_SPOOL_MAX_SIZE_ENV_VAR = "HS_EXTRACT_JSON_SPOOL_MAX_SIZE"
S3_ZONE_CONFIG_ENV_VAR = "S3_ZONE_CONFIG"
DEFAULT_JSON_SPOOL_MAX_SIZE = 5 * 1024 * 1024
DEFAULT_S3_EVENT_TIMEOUT = 5.0

logger = logging.getLogger(__name__)


def _normalize_zone_entry(config: dict) -> dict[str, str | list[str] | None]:
    buckets = config.get("buckets")
    bucket_name = config.get("bucket_name")
    if buckets is None and bucket_name:
        buckets = [bucket_name]
    elif isinstance(buckets, str):
        buckets = [buckets]

    return {
        "endpoint_url": config.get("endpoint_url") or config.get("aws_s3_endpoint_url"),
        "aws_access_key_id": config.get("aws_access_key_id"),
        "aws_secret_access_key": config.get("aws_secret_access_key"),
        "public_endpoint_url": config.get("public_endpoint_url") or config.get("aws_s3_endpoint_url_public", ""),
        "buckets": buckets or [],
    }


def _parse_zone_config() -> dict[str, dict]:
    raw_config = os.environ.get(S3_ZONE_CONFIG_ENV_VAR)
    if not raw_config:
        return {}

    try:
        parsed = json.loads(raw_config)
    except json.JSONDecodeError:
        parsed = ast.literal_eval(raw_config)

    if not isinstance(parsed, dict):
        return {}

    normalized: dict[str, dict] = {}
    for zone, config in parsed.items():
        if isinstance(config, dict):
            normalized[zone] = _normalize_zone_entry(config)
    return normalized


def _create_s3_client(config: dict) -> boto3.client:
    return boto3.client(
        's3',
        endpoint_url=config.get("endpoint_url"),
        aws_access_key_id=config.get("aws_access_key_id"),
        aws_secret_access_key=config.get("aws_secret_access_key"),
    )


zone_s3_config: dict[str, dict] = {}
s3_clients: dict[str, boto3.client] = {}


def refresh_s3_clients_from_env() -> None:
    parsed_zone_config = _parse_zone_config()

    zone_s3_config.clear()
    zone_s3_config.update(parsed_zone_config)

    s3_clients.clear()
    s3_clients.update({
        zone: _create_s3_client(config)
        for zone, config in zone_s3_config.items()
        if isinstance(config, dict)
    })

    for zone, _client in s3_clients.items():
        _register_mutation_hooks(_client, zone)


def resolve_zone(zone: str | None) -> str:
    """Resolve an S3 zone, returning empty string if zone is empty or unknown."""
    normalized_zone = (zone or "").strip()
    if not normalized_zone:
        return ""
    if normalized_zone not in zone_s3_config:
        return ""
    return normalized_zone


def get_configured_zones() -> list[str]:
    return list(zone_s3_config.keys())


def _get_s3_client(zone: str):
    resolved_zone = resolve_zone(zone)
    client = s3_clients.get(resolved_zone)
    if client is None:
        raise KeyError(
            f"No S3 client configured for zone '{resolved_zone}'. "
            f"Set {S3_ZONE_CONFIG_ENV_VAR} with this zone."
            f" Available zones: {', '.join(s3_clients.keys())}"
        )
    return client


def get_s3_client(zone: str):
    return _get_s3_client(zone)


def get_public_endpoint_url(zone: str) -> str:
    resolved_zone = resolve_zone(zone)
    zone_config = zone_s3_config.get(resolved_zone)
    if zone_config is None:
        raise KeyError(
            f"No zone config found for zone '{resolved_zone}'. "
            f"Set {S3_ZONE_CONFIG_ENV_VAR} with this zone."
            f" Available zones: {', '.join(zone_s3_config.keys())}"
        )
    public_url = zone_config.get("public_endpoint_url") or zone_config.get("endpoint_url", "")
    return (public_url or "").rstrip("/")


def build_public_url(path: str, zone: str) -> str:
    bucket, key = _split_s3_path(path)
    endpoint = get_public_endpoint_url(zone)
    return f"{endpoint}/{bucket}/{key}"


def _post_s3_event(action: str, bucket: str, object_path: str, zone: str, file_size: int = 0) -> None:
    endpoint = os.environ.get("HS_S3_AUTH_EVENT_ENDPOINT")
    timeout = float(os.environ.get("HS_S3_AUTH_EVENT_TIMEOUT", str(DEFAULT_S3_EVENT_TIMEOUT)))
    username = os.environ.get("HS_S3_AUTH_EVENT_USERNAME", os.environ.get("AWS_ACCESS_KEY_ID", "cuahsi"))
    payload = {
        "action": action,
        "bucket": bucket,
        "object_path": object_path,
        "username": username,
        "user_id": None,
        "file_size": file_size,
        "zone": zone,
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        if response.status_code not in (200, 204):
            logger.error(
                "S3 event endpoint returned %s for action=%s bucket=%s object=%s: %s",
                response.status_code,
                action,
                bucket,
                object_path,
                response.text,
            )
    except requests.RequestException:
        logger.exception(
            "S3 event endpoint request failed for action=%s bucket=%s object=%s",
            action,
            bucket,
            object_path,
        )


def _register_mutation_hooks(client, zone) -> None:
    events = client.meta.events
    if getattr(events, "_hs_mutation_hooks_registered", False):
        return
    events._hs_mutation_hooks_registered = True

    def before_parameter_build(params, model, context, **kwargs):
        operation = getattr(model, 'name', '')
        if operation not in ("PutObject", "DeleteObject", "CompleteMultipartUpload"):
            return

        context["_hs_bucket"] = params.get("Bucket")
        context["_hs_key"] = params.get("Key")
        context["_hs_zone"] = zone
        context["_hs_action"] = {
            "PutObject": "s3:PutObject",
            "DeleteObject": "s3:DeleteObjects",
            "CompleteMultipartUpload": "s3:CompleteMultipartUpload",
        }.get(operation)

    def after_call(http_response, parsed, model, context, **kwargs):
        action = context.get("_hs_action")
        bucket = context.get("_hs_bucket")
        object_path = context.get("_hs_key")
        zone = context.get("_hs_zone")
        status_code = getattr(http_response, "status_code", None)

        if not action or not bucket or not object_path:
            return
        if status_code not in (200, 204):
            return

        _post_s3_event(action=action, bucket=bucket, object_path=object_path, zone=zone, file_size=0)

    events.register("before-parameter-build.s3.PutObject", before_parameter_build)
    events.register("before-parameter-build.s3.DeleteObject", before_parameter_build)
    events.register("before-parameter-build.s3.CompleteMultipartUpload", before_parameter_build)
    events.register("after-call.s3.PutObject", after_call)
    events.register("after-call.s3.DeleteObject", after_call)
    events.register("after-call.s3.CompleteMultipartUpload", after_call)


refresh_s3_clients_from_env()


def _split_s3_path(path: str) -> tuple[str, str]:
    """Split an S3-style bucket/key path into bucket and key."""
    return path.split('/', 1)


def _iter_s3_objects(resource_root_path: str, zone: str) -> Iterator[dict]:
    """Yield S3 objects under the given resource root path page by page."""
    bucket, resource_path = _split_s3_path(resource_root_path)
    client = _get_s3_client(zone)
    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            yield obj


def _build_media_object(bucket: str, key: str, size_bytes: int, checksum: str, zone: str) -> dict:
    """Build a serializable MediaObject payload for a single S3 object."""
    mime_type = mimetypes.guess_type(key)[0]
    _, extension = os.path.splitext(key)
    _, name = os.path.split(key)
    public_endpoint_url = get_public_endpoint_url(zone)
    media_object = MediaObject(
        contentUrl=f"{public_endpoint_url}/{bucket}/{key}",
        name=name,
        sha256=str(checksum),
        contentSize=f"{size_bytes / 1000.00} KB",
        encodingFormat=mime_type if mime_type else extension
    )
    return media_object.model_dump(exclude_none=True)


def _get_object_size_and_checksum(bucket: str, key: str, zone: str) -> tuple[int, str]:
    """Return object size and checksum with fallbacks for incomplete HEAD responses."""
    client = _get_s3_client(zone)
    response = client.head_object(Bucket=bucket, Key=key)

    size_bytes = response.get('ContentLength')
    if size_bytes is None:
        list_response = client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        for obj in list_response.get('Contents', []):
            if obj.get('Key') == key:
                size_bytes = obj.get('Size')
                break

    checksum = response.get('ETag')
    if checksum is None:
        list_response = locals().get('list_response')
        if list_response is None:
            list_response = client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        for obj in list_response.get('Contents', []):
            if obj.get('Key') == key:
                checksum = obj.get('ETag')
                break

    normalized_checksum = str(checksum or 'N/A').strip('"')
    return int(size_bytes), normalized_checksum


def _build_manifest_reference(
    manifest_path: str,
    size_bytes: int,
    from_manifest_file: bool = False,
    zone: str = "",
) -> dict:
    """Build a MediaObject payload that points to the manifest file itself."""
    bucket, key = _split_s3_path(manifest_path)
    public_endpoint_url = get_public_endpoint_url(zone)
    if not from_manifest_file:
        manifest_object = MediaObject(
            contentUrl=f"{public_endpoint_url}/{bucket}/{key}",
            name=os.path.basename(key),
            contentSize=f"{size_bytes / 1000.00} KB",
            encodingFormat="application/json"
        )
        return manifest_object.model_dump(exclude_none=True)
    else:
        # Use the existing manifest file to build the reference media object
        size_bytes, checksum = _get_object_size_and_checksum(bucket, key, zone)
        manifest_object = _build_media_object(bucket, key, size_bytes, checksum, zone)
        return manifest_object


def _build_has_part_reference(parts_path: str, zone: str) -> dict:
    """Build a HasPart payload that points to the has_parts.json file."""
    bucket, key = _split_s3_path(parts_path)
    public_endpoint_url = get_public_endpoint_url(zone)
    has_part = HasPart(
        url=f"{public_endpoint_url}/{bucket}/{key}",
    )
    return has_part.model_dump(exclude_none=True)


def _get_json_spool_max_size() -> int:
    """Resolve the spool size for streamed JSON sidecars."""
    spool_max_size = os.environ.get(JSON_SPOOL_MAX_SIZE_ENV_VAR)
    return int(spool_max_size) if spool_max_size is not None else DEFAULT_JSON_SPOOL_MAX_SIZE


def _write_json_array(output_path: str, items: Iterator[dict], zone: str) -> int:
    """Stream a JSON array to S3 and return the uploaded size in bytes."""
    bucket_name, key = _split_s3_path(output_path)
    client = _get_s3_client(zone)
    spool_max_size = _get_json_spool_max_size()

    with SpooledTemporaryFile(mode='w+b', max_size=spool_max_size) as stream:
        stream.write(b"[\n")
        first_item = True
        for item in items:
            if not first_item:
                stream.write(b",\n")
            stream.write(b"  ")
            stream.write(json.dumps(item, default=str).encode('utf-8'))
            first_item = False
        stream.write(b"\n]\n")
        size_bytes = stream.tell()
        stream.seek(0)
        client.upload_fileobj(
            stream,
            bucket_name,
            key,
            ExtraArgs={'ContentType': 'application/json'}
        )
        return size_bytes


def iter_file_manifest(
    resource_root_path: str,
    folder_path: str | None = None,
    enabled: bool = False,
    zone: str = "",
) -> Iterator[dict]:
    """Yield file manifest entries lazily for the given resource path."""
    if not enabled:
        return
    bucket, _ = _split_s3_path(resource_root_path)
    if folder_path is None:
        search_path = resource_root_path
    else:
        search_path = f"{resource_root_path}/{folder_path.rstrip('/')}/"
    try:
        for obj in _iter_s3_objects(search_path, zone):
            yield _build_media_object(
                bucket=bucket,
                key=obj['Key'],
                size_bytes=obj['Size'],
                checksum=obj.get('ETag', 'N/A').strip('"'),
                zone=zone,
            )
    except Exception as e:
        print(f"Error retrieving file manifest from {resource_root_path}: {str(e)}")
        raise


def write_file_manifest(
    md: SupportsFileManifest,
    enabled: bool = False,
    fileset_manifest: bool = False
) -> dict | None:
    """Write file_manifest.json to S3 and return a MediaObject pointing to that manifest."""
    manifest_size_bytes = 0
    if not fileset_manifest:
        # generating manifest for resource level associated media
        manifest_path = md.resource_associated_media_jsonld_path
        data_path_prefix = md.resource_contents_path
    else:
        # generating manifest for fileset level associated media
        manifest_path = md.content_type_associated_media_jsonld_path
        data_path_prefix = md.content_type_contents_path
    if md.is_content_file or not exists(manifest_path, md.zone):
        try:
            manifest_size_bytes = _write_json_array(
                manifest_path,
                iter_file_manifest(data_path_prefix, enabled=enabled, zone=md.zone),
                md.zone
            )
            return _build_manifest_reference(manifest_path, manifest_size_bytes, zone=md.zone)
        except Exception as e:
            print(f"Error writing file manifest to {manifest_path}: {str(e)}")
            raise
    else:
        try:
            return _build_manifest_reference(manifest_path, manifest_size_bytes, from_manifest_file=True, zone=md.zone)
        except Exception as e:
            print(f"Error building manifest reference for {manifest_path}: {str(e)}")
            raise


def write_has_part_file(parts_path: str, has_parts: Iterator[dict], zone: str) -> dict:
    """Write has_parts.json to S3 and return a HasPart pointing to that file."""
    try:
        _write_json_array(parts_path, has_parts, zone)
        return _build_has_part_reference(parts_path, zone)
    except Exception as e:
        print(f"Error writing hasPart file to {parts_path}: {str(e)}")
        raise


def write_metadata(metadata_path: str, metadata_json: dict, zone: str) -> None:
    """=
    write metadata to the specified S3 path.
    """
    print(f"writing metadata to {metadata_path}: {metadata_json}")
    bucket_name, key = _split_s3_path(metadata_path)
    client = _get_s3_client(zone)
    try:
        client.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(
            metadata_json, indent=2, default=str))
    except Exception as e:
        print(f"Error writing metadata to {metadata_path}: {str(e)}")
        raise


def delete_metadata(metadata_path: str, zone: str) -> None:
    """
    delete metadata from the specified S3 path.
    """
    bucket_name = metadata_path.split('/')[0]
    key = '/'.join(metadata_path.split('/')[1:])
    client = _get_s3_client(zone)
    try:
        client.delete_object(Bucket=bucket_name, Key=key)
    except Exception as e:
        print(f"Error deleting metadata from {metadata_path}: {str(e)}")
        raise


def load_metadata(metadata_path, zone: str):
    bucket, key = _split_s3_path(metadata_path)
    print(f"Loading metadata from {bucket}/{key}")
    metadata_json = {}
    client = _get_s3_client(zone)
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        with response["Body"] as stream:
            content = stream.read()
            metadata_json = json.loads(content.decode("utf-8"))
    except Exception as e:
        print(f"Metadata file not found {metadata_path}: {str(e)}")
    print(f"Loaded metadata: {metadata_json} from {metadata_path}")
    return metadata_json


def iter_find(path: str, zone: str) -> Iterator[str]:
    """Yield matching S3 keys lazily for the given bucket/prefix path."""
    bucket, resource_path = _split_s3_path(path)
    client = _get_s3_client(zone)
    paginator = client.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
            if 'Contents' not in page:
                continue
            print(f"Processing page with {len(page['Contents'])} items")
            for obj in page['Contents']:
                yield f"{bucket}/{obj['Key']}"
    except Exception as e:
        print(f"path not found {path}: {str(e)}")


def find(path: str, zone: str) -> list[str]:
    keys = []
    for key in iter_find(path, zone):
        keys.append(key)
    print(f"Found files: {keys}")
    return keys


def exists(path: str, zone: str) -> bool:
    """
    Check if a file exists in the S3 bucket.
    """
    bucket, key = _split_s3_path(path)
    client = _get_s3_client(zone)
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error checking existence of {path}: {str(e)}")
        return False
