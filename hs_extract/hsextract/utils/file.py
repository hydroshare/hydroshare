import mimetypes
import os
from hsextract.utils.s3 import _get_object_size_and_checksum, _split_s3_path
from hs_cloudnative_schemas.schema.base import MediaObject


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
