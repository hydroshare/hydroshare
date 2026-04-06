from hsextract.main import ContentType, BaseMetadataObject
import uuid
import pytest

from time import sleep
from tests import (
    assert_manifest_reference,
    read_s3_json,
    write_s3_json,
    assert_has_part_reference,
    s3_path_exists,
)


@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject(use_folder):
    folder_prefix = "test-folder/" if use_folder else ""
    md = BaseMetadataObject(f"test-bucket/resourceid/data/contents/{folder_prefix}file.txt", True)
    assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_prefix}file.txt"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.UNKNOWN
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == "test-bucket/resourceid/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == "test-bucket/resourceid/.hsjsonld/has_parts.json"

    assert md.content_type_md_jsonld_path is None
    assert md.content_type_md_path is None
    assert md.content_type_contents_path is None
    assert md.content_type_main_file_path is None
    assert md.content_type_md_user_path is None
    assert md._content_type_associated_media is None



@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_extraction(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "test-folder/" if use_folder else ""
    print(resource_id)
    # Stage system metadata to test
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/{folder_prefix}file.txt",
                  {"file_metadata": "this is file metadata"})

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert result_resource_metadata[
        "system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)

    write_s3_json(f"test-bucket/{resource_id}/data/contents/{folder_prefix}file-1.txt",
                  {"file_metadata": "this is file-1 metadata"})
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=2)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)


def test_resource_extraction_without_data_files_writes_empty_sidecars():
    resource_id = str(uuid.uuid4())
    write_s3_json(
        f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json",
        {"system_metadata": "this is system metadata"},
    )
    write_s3_json(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json",
        {"user_metadata": "this is user metadata"},
    )

    sleep(1)

    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    )

    assert result_resource_metadata["system_metadata"] == "this is system metadata"
    assert result_resource_metadata["user_metadata"] == "this is user metadata"
    file_manifest_path = f"test-bucket/{resource_id}/.hsjsonld/file_manifest.json"
    has_parts_path = f"test-bucket/{resource_id}/.hsjsonld/has_parts.json"
    assert s3_path_exists(file_manifest_path) is True
    assert s3_path_exists(has_parts_path) is True
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=0)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)

    result_file_manifest = read_s3_json(file_manifest_path)
    result_has_parts = read_s3_json(has_parts_path)

    assert result_file_manifest == []
    assert result_has_parts == []


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_extraction_system_metadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "test-folder/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/{folder_prefix}file.txt",
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
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_extraction_user_metadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "test-folder/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    write_s3_json(f"test-bucket/{resource_id}/data/contents/{folder_prefix}file.txt",
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
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)
