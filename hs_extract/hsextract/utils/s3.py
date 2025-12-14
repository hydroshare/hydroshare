import json
import mimetypes
import os

import boto3
from hs_cloudnative_schemas.schema.base import MediaObject

s3_config = {
    "endpoint_url": os.environ.get("AWS_S3_ENDPOINT_URL", "https://s3.beta.hydroshare.org"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
}
s3_client = boto3.client('s3', **s3_config)


def write_metadata(metadata_path: str, metadata_json: dict) -> None:
    """=
    write metadata to the specified S3 path.
    """
    print(f"writing metadata to {metadata_path}: {metadata_json}")
    bucket_name = metadata_path.split('/')[0]
    key = '/'.join(metadata_path.split('/')[1:])
    try:
        s3_client.put_object(Bucket=bucket_name, Key=key, Body=json.dumps(
            metadata_json, indent=2, default=str))
    except Exception as e:
        print(f"Error writing metadata to {metadata_path}: {e}")
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
        print(f"Error deleting metadata from {metadata_path}: {e}")
        raise


def load_metadata(metadata_path):
    bucket, key = metadata_path.split('/', 1)
    print(f"Loading metadata from {bucket}/{key}")
    metadata_json = {}
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        with response["Body"] as stream:
            content = stream.read()
            metadata_json = json.loads(content.decode("utf-8"))
    except Exception as e:
        print(f"Metadata file not found {metadata_path}: {e}")
    print(f"Loaded metadata: {metadata_json} from {metadata_path}")
    return metadata_json


def retrieve_file_manifest(resource_root_path: str):
    """
    list files from the S3 bucket.
    """
    paginator = s3_client.get_paginator('list_objects_v2')
    bucket, resource_path = resource_root_path.split('/', 1)
    print(f"Retrieving file manifest from S3 at {bucket}/{resource_path}")
    file_manifest = []
    limit = 15
    count = 0
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if count >= limit:
                        print(f"File manifest limit of {limit} reached, stopping retrieval.")
                        return file_manifest
                    count += 1
                    key = obj['Key']
                    size = obj['Size']
                    size = f"{obj['Size'] / 1000.00} KB"
                    # TODO check this is actually sha256, I think it is etag which
                    # is md5
                    checksum = obj.get('ETag', 'N/A').strip('"')
                    mime_type = mimetypes.guess_type(key)[0]
                    _, extension = os.path.splitext(key)
                    mime_type = mime_type if mime_type else extension
                    _, name = os.path.split(key)
                    content_url = f"{os.environ['AWS_S3_ENDPOINT_URL']}/{bucket}/{key}"
                    media_object = MediaObject(
                        contentUrl=content_url,
                        name=name,
                        sha256=str(checksum),
                        contentSize=size,
                        encodingFormat=mime_type
                    )
                    file_manifest.append(
                        media_object.model_dump(exclude_none=True))
    except Exception as e:
        print(f"Error retrieving file manifest from {resource_root_path}: {e}")
    print(f"Retrieved file manifest: {file_manifest} from {resource_root_path}")
    return file_manifest


def find(path: str) -> list[str]:
    paginator = s3_client.get_paginator('list_objects_v2')
    bucket, resource_path = path.split('/', 1)
    keys = []
    print(f"Finding files in S3 at {bucket}/{resource_path}")
    try:
        for page in paginator.paginate(Bucket=bucket, Prefix=resource_path):
            print(f"Found files in S3 at {bucket}/{resource_path}")
            if 'Contents' in page:
                print(f"Processing page with {len(page['Contents'])} items")
                for obj in page['Contents']:
                    key = obj['Key']
                    key = f"{bucket}/{key}"
                    keys.append(key)
    except Exception as e:
        print(f"path not found {path}: {e}")
    print(f"Found files: {keys}")
    return keys


def exists(path: str) -> bool:
    """
    Check if a file exists in the S3 bucket.
    """
    bucket, key = path.split('/', 1)
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception as e:
        print(f"Error checking existence of {path}: {e}")
        return False
