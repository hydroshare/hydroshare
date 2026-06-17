from __future__ import annotations
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
DEFAULT_JSON_SPOOL_MAX_SIZE = 5 * 1024 * 1024
DEFAULT_S3_EVENT_ENDPOINT = "http://hs-s3-auth/s3/event/"
DEFAULT_S3_EVENT_TIMEOUT = 5.0

logger = logging.getLogger(__name__)

DEFAULT_SETTINGS_FILE = "/app/hydroshare/settings.py"
DEFAULT_ZONE_NAME = "hydroshare"


def _build_s3_config() -> dict:
    endpoint_url = os.environ.get("AWS_S3_ENDPOINT_URL", "https://s3.beta.hydroshare.org")
    access_key = os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
    public_endpoint_url = os.environ.get("AWS_S3_ENDPOINT_URL_PUBLIC", endpoint_url)
    return {
        "zone_name": os.environ.get("HS_S3_ZONE_NAME", DEFAULT_ZONE_NAME),
        "endpoint_url": endpoint_url,
        "aws_access_key_id": access_key,
        "aws_secret_access_key": secret_key,
        "public_endpoint_url": public_endpoint_url,
    }


s3_config = _build_s3_config()
s3_client = boto3.client(
    's3',
    endpoint_url=s3_config["endpoint_url"],
    aws_access_key_id=s3_config["aws_access_key_id"],
    aws_secret_access_key=s3_config["aws_secret_access_key"],
)


def _resolve_s3_event_endpoint() -> str:
    explicit_endpoint = os.environ.get("HS_S3_AUTH_EVENT_ENDPOINT")
    if explicit_endpoint:
        return explicit_endpoint

    auth_service_url = os.environ.get("AUTH_SERVICE_URL")
    if auth_service_url:
        return f"{auth_service_url.rstrip('/')}/s3/event/"

    return DEFAULT_S3_EVENT_ENDPOINT


def _post_s3_event(action: str, bucket: str, object_path: str, file_size: int = 0) -> None:
    endpoint = _resolve_s3_event_endpoint()
    timeout = float(os.environ.get("HS_S3_AUTH_EVENT_TIMEOUT", str(DEFAULT_S3_EVENT_TIMEOUT)))
    username = os.environ.get("HS_S3_AUTH_EVENT_USERNAME", os.environ.get("AWS_ACCESS_KEY_ID", "cuahsi"))
    payload = {
        "action": action,
        "bucket": bucket,
        "object_path": object_path,
        "username": username,
        "user_id": None,
        "file_size": file_size,
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


def _register_mutation_hooks(client) -> None:
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
        context["_hs_action"] = {
            "PutObject": "s3:PutObject",
            "DeleteObject": "s3:DeleteObjects",
            "CompleteMultipartUpload": "s3:CompleteMultipartUpload",
        }.get(operation)

    def after_call(http_response, parsed, model, context, **kwargs):
        action = context.get("_hs_action")
        bucket = context.get("_hs_bucket")
        object_path = context.get("_hs_key")
        status_code = getattr(http_response, "status_code", None)

        if not action or not bucket or not object_path:
            return
        if status_code not in (200, 204):
            return

        _post_s3_event(action=action, bucket=bucket, object_path=object_path, file_size=0)

    events.register("before-parameter-build.s3.PutObject", before_parameter_build)
    events.register("before-parameter-build.s3.DeleteObject", before_parameter_build)
    events.register("before-parameter-build.s3.CompleteMultipartUpload", before_parameter_build)
    events.register("after-call.s3.PutObject", after_call)
    events.register("after-call.s3.DeleteObject", after_call)
    events.register("after-call.s3.CompleteMultipartUpload", after_call)


_register_mutation_hooks(s3_client)


def _split_s3_path(path: str) -> tuple[str, str]:
    """Split an S3-style bucket/key path into bucket and key."""
    return path.split('/', 1)


def _iter_s3_objects(resource_root_path: str) -> Iterator[dict]:
    """Yield S3 objects under the given resource root path page by page."""
    paginator = s3_client.get_paginator('list_objects_v2')
    bucket, resource_path = _split_s3_path(resource_root_path)
    for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            yield obj


def _build_media_object(bucket: str, key: str, size_bytes: int, checksum: str) -> dict:
    """Build a serializable MediaObject payload for a single S3 object."""
    mime_type = mimetypes.guess_type(key)[0]
    _, extension = os.path.splitext(key)
    _, name = os.path.split(key)
    media_object = MediaObject(
        contentUrl=f"{s3_config['public_endpoint_url']}/{bucket}/{key}",
        name=name,
        sha256=str(checksum),
        contentSize=f"{size_bytes / 1000.00} KB",
        encodingFormat=mime_type if mime_type else extension
    )
    return media_object.model_dump(exclude_none=True)


def _get_object_size_and_checksum(bucket: str, key: str) -> tuple[int, str]:
    """Return object size and checksum with fallbacks for incomplete HEAD responses."""
    response = s3_client.head_object(Bucket=bucket, Key=key)

    size_bytes = response.get('ContentLength')
    if size_bytes is None:
        list_response = s3_client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        for obj in list_response.get('Contents', []):
            if obj.get('Key') == key:
                size_bytes = obj.get('Size')
                break

    checksum = response.get('ETag')
    if checksum is None:
        list_response = locals().get('list_response')
        if list_response is None:
            list_response = s3_client.list_objects_v2(Bucket=bucket, Prefix=key, MaxKeys=1)
        for obj in list_response.get('Contents', []):
            if obj.get('Key') == key:
                checksum = obj.get('ETag')
                break

    if size_bytes is None:
        body_response = s3_client.get_object(Bucket=bucket, Key=key)
        with body_response['Body'] as stream:
            size_bytes = len(stream.read())

    normalized_checksum = str(checksum or 'N/A').strip('"')
    return int(size_bytes), normalized_checksum


def _build_manifest_reference(manifest_path: str, size_bytes: int, from_manifest_file: bool = False) -> dict:
    """Build a MediaObject payload that points to the manifest file itself."""
    bucket, key = _split_s3_path(manifest_path)
    if not from_manifest_file:
        manifest_object = MediaObject(
            contentUrl=f"{s3_config['public_endpoint_url']}/{bucket}/{key}",
            name=os.path.basename(key),
            contentSize=f"{size_bytes / 1000.00} KB",
            encodingFormat="application/json"
        )
        return manifest_object.model_dump(exclude_none=True)
    else:
        # Use the existing manifest file to build the reference media object
        size_bytes, checksum = _get_object_size_and_checksum(bucket, key)
        manifest_object = _build_media_object(bucket, key, size_bytes, checksum)
        return manifest_object


def _build_has_part_reference(parts_path: str) -> dict:
    """Build a HasPart payload that points to the has_parts.json file."""
    bucket, key = _split_s3_path(parts_path)
    has_part = HasPart(
        url=f"{s3_config['public_endpoint_url']}/{bucket}/{key}",
    )
    return has_part.model_dump(exclude_none=True)


def _get_json_spool_max_size() -> int:
    """Resolve the spool size for streamed JSON sidecars."""
    spool_max_size = os.environ.get(JSON_SPOOL_MAX_SIZE_ENV_VAR)
    return int(spool_max_size) if spool_max_size is not None else DEFAULT_JSON_SPOOL_MAX_SIZE


def _write_json_array(output_path: str, items: Iterator[dict]) -> int:
    """Stream a JSON array to S3 and return the uploaded size in bytes."""
    bucket_name, key = _split_s3_path(output_path)
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
        s3_client.upload_fileobj(
            stream,
            bucket_name,
            key,
            ExtraArgs={'ContentType': 'application/json'}
        )
        return size_bytes


def iter_file_manifest(
    resource_root_path: str,
    folder_path: str | None = None,
    enabled: bool = False
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
        for obj in _iter_s3_objects(search_path):
            yield _build_media_object(
                bucket=bucket,
                key=obj['Key'],
                size_bytes=obj['Size'],
                checksum=obj.get('ETag', 'N/A').strip('"')
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
    if md.is_content_file or not exists(manifest_path):
        try:
            manifest_size_bytes = _write_json_array(
                manifest_path,
                iter_file_manifest(data_path_prefix, enabled=enabled),
            )
            return _build_manifest_reference(manifest_path, manifest_size_bytes)
        except Exception as e:
            print(f"Error writing file manifest to {manifest_path}: {str(e)}")
            raise
    else:
        try:
            return _build_manifest_reference(manifest_path, manifest_size_bytes, from_manifest_file=True)
        except Exception as e:
            print(f"Error building manifest reference for {manifest_path}: {str(e)}")
            raise


def write_has_part_file(parts_path: str, has_parts: Iterator[dict]) -> dict:
    """Write has_parts.json to S3 and return a HasPart pointing to that file."""
    try:
        _write_json_array(parts_path, has_parts)
        return _build_has_part_reference(parts_path)
    except Exception as e:
        print(f"Error writing hasPart file to {parts_path}: {str(e)}")
        raise


def write_metadata(metadata_path: str, metadata_json: dict) -> None:
    """=
    write metadata to the specified S3 path.
    """
    print(f"writing metadata to {metadata_path}: {metadata_json}")
    bucket_name, key = _split_s3_path(metadata_path)
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(
            metadata_json, indent=2, default=str))
    except Exception as e:
        print(f"Error writing metadata to {metadata_path}: {str(e)}")
        raise


def delete_metadata(metadata_path: str) -> None:
    """
    delete metadata from the specified S3 path.
    """
    bucket_name = metadata_path.split('/')[0]
    key = '/'.join(metadata_path.split('/')[1:])
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=key)
    except Exception as e:
        print(f"Error deleting metadata from {metadata_path}: {str(e)}")
        raise


def load_metadata(metadata_path):
    bucket, key = _split_s3_path(metadata_path)
    print(f"Loading metadata from {bucket}/{key}")
    metadata_json = {}
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        with response["Body"] as stream:
            content = stream.read()
            metadata_json = json.loads(content.decode("utf-8"))
    except Exception as e:
        print(f"Metadata file not found {metadata_path}: {str(e)}")
    print(f"Loaded metadata: {metadata_json} from {metadata_path}")
    return metadata_json


def iter_find(path: str) -> Iterator[str]:
    """Yield matching S3 keys lazily for the given bucket/prefix path."""
    paginator = s3_client.get_paginator('list_objects_v2')
    bucket, resource_path = _split_s3_path(path)
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
            if 'Contents' not in page:
                continue
            print(f"Processing page with {len(page['Contents'])} items")
            for obj in page['Contents']:
                yield f"{bucket}/{obj['Key']}"
    except Exception as e:
        print(f"path not found {path}: {str(e)}")


def find(path: str) -> list[str]:
    keys = []
    for key in iter_find(path):
        keys.append(key)
    print(f"Found files: {keys}")
    return keys


def exists(path: str) -> bool:
    """
    Check if a file exists in the S3 bucket.
    """
    bucket, key = _split_s3_path(path)
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error checking existence of {path}: {str(e)}")
        return False
