import json
import os

from hsextract.utils.s3 import get_s3_client
from hsextract.utils.s3 import refresh_s3_clients_from_env


os.environ.setdefault(
    "S3_ZONE_CONFIG",
    json.dumps({
        "hydroshare": {
            "bucket_name": "resource",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        },
        "published": {  # the publisher hydroshare user must be updated to use this zone, see PUBLISHER_USER_NAME
            "bucket_name": "published",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        },
        "ciroh": {
            "bucket_name": "ciroh",
            "aws_s3_endpoint_url": "http://minio:9000",
            "aws_access_key_id": "cuahsi",
            "aws_secret_access_key": "devpassword",
            "aws_s3_endpoint_url_public": "http://localhost:9000"
        }
    }),
)

refresh_s3_clients_from_env()
TEST_ZONE = "hydroshare"


s3_client = get_s3_client(TEST_ZONE)


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
