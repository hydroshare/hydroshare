from hsextract.main import ContentType, BaseMetadataObject
import uuid

from time import sleep
from tests import read_s3_json, write_s3_json


def test_metadataobject():
    md = BaseMetadataObject("test-bucket/resourceid/data/contents/file.txt", True)
    assert md.file_object_path == "test-bucket/resourceid/data/contents/file.txt"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type_md_jsonld_path is None
    assert md.content_type == ContentType.UNKNOWN
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"


def test_resource_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    # Stage system metadata to test
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/file.txt",
                  {"file_metadata": "this is file metadata"})

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == "file.txt"


def test_resource_extraction_system_metadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/file.txt",
                  {"file_metadata": "this is file metadata"})
    sleep(1)
    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert result_resource_metadata["system_metadata"] == "this is system metadata"
    # Stage system metadata to test
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata added last"})
    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata added last"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == "file.txt"


def test_resource_extraction_user_metadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/file.txt",
                  {"file_metadata": "this is file metadata"})
    sleep(1)

    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert result_resource_metadata["user_metadata"] == "this is user metadata"

    # Stage user metadata to test
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata added last"})
    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata added last"
    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == "file.txt"
