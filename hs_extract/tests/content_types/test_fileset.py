from time import sleep

import uuid
import pytest

from tests import (
    assert_has_part_reference,
    assert_manifest_reference,
    assert_manifest_reference_fileset,
    s3_client,
    read_s3_json,
    write_s3_json
)
from hsextract.content_types.models import ContentType
from hsextract.content_types.fileset.models import FileSetMetadataObject
from hsextract.content_types import determine_metadata_object_from_user_metadata


@pytest.mark.parametrize("use_nested_folder", [True, False])
def test_metadataobject(use_nested_folder):
    folder_path = "folder_aggregation/test_folder" if use_nested_folder else "folder_aggregation"
    file_name = "testfile.txt"
    md = FileSetMetadataObject(
            f"test-bucket/resourceid/data/contents/{folder_path}/{file_name}", True
        )

    assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_path}"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.FILE_SET
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"

    assert md.content_type_md_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{folder_path}/dataset_metadata.json"
    manifest_file_path = f"{folder_path}/file_manifest.json"
    assert md.content_type_associated_media_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{manifest_file_path}"
    assert md.content_type_md_path == f"test-bucket/resourceid/.hsmetadata/{folder_path}/user_metadata.json"
    assert md.content_type_contents_path == f"test-bucket/resourceid/data/contents/{folder_path}"
    assert md.content_type_main_file_path == f"test-bucket/resourceid/data/contents/{folder_path}"


@pytest.mark.parametrize("use_nested_folder", [True, False])
def test_metadataobject_from_user_metadata(use_nested_folder):
    resource_id = str(uuid.uuid4())
    folder_path = "folder_aggregation/test_folder" if use_nested_folder else "folder_aggregation"
    user_meta_file_name = "user_metadata.json"
    user_metadata_path = f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/{user_meta_file_name}"

    write_s3_json(user_metadata_path, {"user_metadata": "this is fileset user metadata"})
    # Wait for metadata to be consistent
    sleep(1)
    md = determine_metadata_object_from_user_metadata(
            f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/{user_meta_file_name}", True
        )

    assert isinstance(md, FileSetMetadataObject)
    assert md.file_object_path == f"test-bucket/{resource_id}/data/contents/{folder_path}"
    assert md.file_updated is True
    assert md.resource_contents_path == f"test-bucket/{resource_id}/data/contents"
    assert md.resource_md_path == f"test-bucket/{resource_id}/.hsmetadata"
    assert md.resource_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld"
    assert md.content_type == ContentType.FILE_SET
    assert md.system_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    assert md.content_type_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/{folder_path}/dataset_metadata.json"
    manifest_file_path = f"{folder_path}/file_manifest.json"
    assert md.content_type_associated_media_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/{manifest_file_path}"
    assert md.content_type_md_path == f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/user_metadata.json"
    assert md.content_type_contents_path == f"test-bucket/{resource_id}/data/contents/{folder_path}"
    assert md.content_type_main_file_path == f"test-bucket/{resource_id}/data/contents/{folder_path}"


@pytest.mark.parametrize("user_meta_file", [True, False])
@pytest.mark.parametrize("use_nested_folder", [True, False])
def test_fileset_is_content_type(use_nested_folder, user_meta_file):
    resource_id = str(uuid.uuid4())
    folder_path = "folder_aggregation/test_folder" if use_nested_folder else "folder_aggregation"
    content_path = f"test-bucket/{resource_id}/data/contents/{folder_path}/testfile.txt"
    user_metadata_path = f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/user_metadata.json"
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_path}/testfile.txt")
    
    if user_meta_file:
        write_s3_json(user_metadata_path, {"user_metadata": "this is fileset user metadata"})
    sleep(1)

    assert FileSetMetadataObject.is_content_type(content_path) is user_meta_file


@pytest.mark.parametrize("use_nested_folder", [True, False])
def test_fileset(use_nested_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_path = "folder_aggregation/test_folder" if use_nested_folder else "folder_aggregation"
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/user_metadata.json", {
                  "user_metadata": "this is fileset user metadata"})
    sleep(1)
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_path}/testfile.txt")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_path}/dataset_metadata.json")

    result_fileset_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_path}/dataset_metadata.json")
    assert len(result_fileset_metadata["associatedMedia"]) == 1
    assert result_fileset_metadata["associatedMedia"][0]["name"] == "file_manifest.json"
    assert_manifest_reference_fileset(result_fileset_metadata, resource_id, folder_path,
                                      "test-bucket", expected_media_obj_count=1)
    assert len(result_fileset_metadata["isPartOf"]) == 1
    assert result_fileset_metadata["isPartOf"][0]['url'].endswith("dataset_metadata.json")
    assert result_fileset_metadata["user_metadata"] == "this is fileset user metadata"


@pytest.mark.parametrize("use_nested_folder", [True, False])
def test_fileset_user_metadata(use_nested_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_path = "folder_aggregation/test_folder" if use_nested_folder else "folder_aggregation"
    print(resource_id)
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_path}/testfile.txt")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)
    result_has_parts = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert result_has_parts == []

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_path}/user_metadata.json", {
                  "user_metadata": "this is fileset user metadata"})
    sleep(1)
    result_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/{folder_path}/dataset_metadata.json"
    result_fileset_metadata = read_s3_json(result_metadata_path)
    assert result_fileset_metadata["user_metadata"] == "this is fileset user metadata"
