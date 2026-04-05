import json
import os
import boto3
import subprocess


s3_config = {
    "endpoint_url": os.environ.get("AWS_S3_ENDPOINT", "http://minio:9000"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "cuahsi"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "devpassword")
}
s3_client = boto3.client('s3', **s3_config)
# Create a bucket for testing purposes
try:
    s3_client.create_bucket(Bucket="test-bucket")
except s3_client.exceptions.BucketAlreadyOwnedByYou:
    pass
    # Set up S3 event notifications for put and delete events using mc
try:
    subprocess.run([
        "mc", "event", "add", "hydroshare/test-bucket",
        "arn:minio:sqs::RESOURCEFILE:kafka",
        "--event", "put,delete"
    ], check=True)
except subprocess.CalledProcessError as e:
    print(f"Failed to set up S3 event notifications: {e}")


def read_s3_json(path: str):
    bucket, key = path.split("/", 1)
    response = s3_client.get_object(
        Bucket=bucket,
        Key=key
    )
    file_content = response['Body'].read().decode('utf-8')
    metadata_json = json.loads(file_content)
    return metadata_json


def write_s3_json(path: str, metadata_json: dict):
    bucket, key = path.split("/", 1)
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(metadata_json, indent=2).encode('utf-8'),
        ContentType='application/json'
    )


def s3_path_exists(path: str):
    bucket, key = path.split("/", 1)
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        return True
    except Exception:
        return False


def assert_manifest_reference(resource_metadata: dict, resource_id: str, bucket: str,
                              expected_media_obj_count: int = 0):
    associated_media_file_reference = resource_metadata["associatedMedia"]
    assert len(associated_media_file_reference) == 1
    assert associated_media_file_reference[0]["name"] == "file_manifest.json"
    assert associated_media_file_reference[0]["encodingFormat"] == "application/json"
    hsjsonld_path = f"{bucket}/{resource_id}/.hsjsonld/file_manifest.json"
    assert associated_media_file_reference[0]["contentUrl"].endswith(hsjsonld_path)
    file_manifest = read_s3_json(hsjsonld_path)
    assert len(file_manifest) == expected_media_obj_count


def assert_manifest_reference_fileset(fileset_metadata: dict, resource_id: str, folder_path: str, bucket: str,
                                      expected_media_obj_count: int = 0):
    associated_media_file_reference = fileset_metadata["associatedMedia"]
    assert len(associated_media_file_reference) == 1
    assert associated_media_file_reference[0]["name"] == "file_manifest.json"
    assert associated_media_file_reference[0]["encodingFormat"] == "application/json"
    hsjsonld_path = f"{bucket}/{resource_id}/.hsjsonld/{folder_path}/file_manifest.json"
    assert associated_media_file_reference[0]["contentUrl"].endswith(hsjsonld_path)
    file_manifest = read_s3_json(hsjsonld_path)
    assert len(file_manifest) == expected_media_obj_count

def assert_has_part_reference(resource_metadata: dict, resource_id: str, bucket: str,
                              expected_has_part_count: int = 0):
    has_part = resource_metadata["hasPart"]
    assert len(has_part) == 1
    hsjsonld_path = f"{bucket}/{resource_id}/.hsjsonld/has_parts.json"
    assert has_part[0]["url"].endswith(hsjsonld_path)
    has_parts_file = read_s3_json(hsjsonld_path)
    assert len(has_parts_file) == expected_has_part_count
