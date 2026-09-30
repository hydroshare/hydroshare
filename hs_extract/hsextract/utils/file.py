import mimetypes
import os
from hsextract.utils.s3 import get_s3_client, _split_s3_path
from hs_cloudnative_schemas.schema.base import MediaObject


def _get_object_size_and_checksum(bucket: str, key: str, zone: str) -> tuple[int, str]:
    """Read object size and checksum from S3 metadata with list fallback."""
    client = get_s3_client(zone)
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


def file_metadata(path: str, zone: str):
    # if path == "/tmp/hs_user_meta.json":
    #    return file_metadata_local(path)
    bucket, key = _split_s3_path(path)
    if not key or path.endswith('/'):
        checksum = 'N/A'
        size = "0 KB"
    else:
        size_bytes, checksum = _get_object_size_and_checksum(bucket, key, zone)
        size = f"{size_bytes / 1000.00} KB"
    mime_type = mimetypes.guess_type(path)[0]
    _, extension = os.path.splitext(path)
    mime_type = mime_type if mime_type else extension
    _, name = os.path.split(path)
    return MediaObject(contentUrl=path,
                       name=name,
                       sha256=str(checksum),
                       contentSize=size,
                       encodingFormat=mime_type)
