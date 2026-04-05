from __future__ import annotations
import json
import mimetypes
import os
from tempfile import SpooledTemporaryFile
from typing import Iterator, Protocol, TYPE_CHECKING

import boto3
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

s3_config = {
    "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL", "https://s3.beta.hydroshare.org"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
}
s3_client = boto3.client('s3', **s3_config)


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
        contentUrl=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{bucket}/{key}",
        name=name,
        sha256=str(checksum),
        contentSize=f"{size_bytes / 1000.00} KB",
        encodingFormat=mime_type if mime_type else extension
    )
    return media_object.model_dump(exclude_none=True)


def _build_manifest_reference(manifest_path: str, size_bytes: int, from_manifest_file: bool = False) -> dict:
    """Build a MediaObject payload that points to the manifest file itself."""
    bucket, key = _split_s3_path(manifest_path)
    if not from_manifest_file:
        manifest_object = MediaObject(
            contentUrl=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{bucket}/{key}",
            name=os.path.basename(key),
            contentSize=f"{size_bytes / 1000.00} KB",
            encodingFormat="application/json"
        )
        return manifest_object.model_dump(exclude_none=True)
    else:
        # Use the existing manifest file to build the reference media object
        response = s3_client.head_object(Bucket=bucket, Key=key)
        size_bytes = response['ContentLength']
        checksum = response.get('ETag', 'N/A').strip('"')
        manifest_object = _build_media_object(bucket, key, size_bytes, checksum)
        return manifest_object


def _build_has_part_reference(parts_path: str) -> dict:
    """Build a HasPart payload that points to the has_parts.json file."""
    bucket, key = _split_s3_path(parts_path)
    has_part = HasPart(
        url=f"{os.environ['AWS_S3_ENDPOINT_URL']}/{bucket}/{key}",
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


def iter_file_manifest(resource_root_path: str, folder_path: str | None = None, enabled: bool = False) -> Iterator[dict]:
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


def retrieve_file_manifest(resource_root_path: str, enabled: bool = False):
    """
    list files from the S3 bucket.
    """
    file_manifest = []
    for media_object in iter_file_manifest(resource_root_path, enabled=enabled):
        file_manifest.append(media_object)
    return file_manifest


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
