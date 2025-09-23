import json
import os
from time import sleep
import boto3

from hsextract.main import ContentType, MetadataObject
import pytest
import uuid

s3_config = {
    "endpoint_url": os.environ.get("AWS_S3_ENDPOINT", "https://s3.beta.hydroshare.org"),
    "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "YOUR_ACCESS_KEY"),
    "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "YOUR_SECRET_KEY")
}
s3_client = boto3.client('s3', **s3_config)


def test_metadataobject():
    md = MetadataObject("test-bucket/resourceid/data/contents/file.txt", True)
    assert md.file_object_path == "test-bucket/resourceid/data/contents/file.txt"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "hsmetadata/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "hsmetadata/resourceid/.hsjsonld"
    assert md.content_type_md_jsonld_path is None
    assert md.content_type == ContentType.UNKNOWN
    assert md.system_metadata_path == "hsmetadata/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "hsmetadata/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_path == "hsmetadata/resourceid/.hsjsonld/dataset_metadata.json"


@pytest.fixture
def s3_resource_setup_teardown():
    # Setup: Create a temporary bucket for testing
    buckets = ["hsmetadata", "admin"]
    try:
        for bucket in buckets:
            s3_client.create_bucket(Bucket=bucket)
    except Exception:
        pass
    '''
    test_file_output_dir = "test_files/"
    for root, _, files in os.walk(test_file_output_dir):
        for file in files:
            file_path = os.path.join(root, file)
            s3_key = os.path.join("resource_id", "data", "contents", file)
            with open(file_path, "rb") as f:
                s3_client.upload_fileobj(f, test_bucket, s3_key)
    '''
    yield
    # Teardown: Remove all files from the test bucket
    for bucket in buckets:
        response = s3_client.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3_client.delete_object(Bucket=bucket, Key=obj['Key'])
        s3_client.delete_bucket(Bucket=bucket)


def test_resource_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    # Stage system metadata to test
    write_s3_json(f"hsmetadata/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"hsmetadata/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"admin/{resource_id}/data/contents/file.txt",
                  {"file_metadata": "this is file metadata"})

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"hsmetadata/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == "file.txt"


def test_resource_netcdf_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    # Stage system metadata to test
    write_s3_json(f"hsmetadata/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"hsmetadata/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})
    write_s3_json(f"hsmetadata/{resource_id}/.hsmetadata/netcdf_valid.nc.user_metadata.json", {
                  "user_metadata": "this is netcdf user metadata"})

    sleep(1)
    with open("tests/test_files/netcdf/netcdf_valid.nc", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/netcdf_valid.nc")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"hsmetadata/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("netcdf_valid.nc.json")

    result_netcdf_metadata = read_s3_json(
        f"hsmetadata/{resource_id}/.hsjsonld/netcdf_valid.nc.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0].endswith("dataset_metadata.json")
    assert result_netcdf_metadata[
        "user_metadata"] == "this is netcdf user metadata"


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
