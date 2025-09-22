import mimetypes
import os
from hsextract import s3_client as s3
from hsextract.hs_cn_schemas.schema.src.base import MediaObject


def file_metadata(path: str):
    # if path == "/tmp/hs_user_meta.json":
    #    return file_metadata_local(path)
    checksum = s3.checksum(path)
    if s3.isdir(path):
        size = "0 KB"
    else:
        size = f"{s3.info(path)['size'] / 1000.00} KB"
    mime_type = mimetypes.guess_type(path)[0]
    _, extension = os.path.splitext(path)
    mime_type = mime_type if mime_type else extension
    _, name = os.path.split(path)
    return MediaObject(contentUrl=path,
                       name=name,
                       sha256=str(checksum),
                       contentSize=size,
                       encodingFormat=mime_type), None
