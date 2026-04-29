import mimetypes
import os

from hsextract.utils.s3 import s3_client as s3
from hs_cloudnative_schemas.schema.base import MediaObject


def file_metadata(path: str):
    bucket, key = path.split("/", 1)
    response = s3.head_object(Bucket=bucket, Key=key)
    checksum = response.get('ETag', 'N/A').strip('"')
    size = f"{response.get('ContentLength', 0) / 1000.00} KB"
    mime_type = mimetypes.guess_type(path)[0]
    _, extension = os.path.splitext(path)
    mime_type = mime_type if mime_type else extension
    _, name = os.path.split(path)
    return MediaObject(contentUrl=path,
                       name=name,
                       sha256=str(checksum),
                       contentSize=size,
                       encodingFormat=mime_type)
