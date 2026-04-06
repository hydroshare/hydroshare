import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json
from hsextract.content_types.models import ContentType
from hsextract.content_types.singlefile.models import SingleFileMetadataObject


@pytest.mark.parametrize("user_meta_file", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject(use_folder, user_meta_file):
    folder_prefix = "test-folder/" if use_folder else ""
    if not user_meta_file:
        file_name = "testfile.txt"
        user_meta_file_name = f"{file_name}.user_metadata.json"
    else:
        file_name = "testfile.txt.user_metadata.json"
        user_meta_file_name = file_name

    if not user_meta_file:
        md = SingleFileMetadataObject(
            f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}", True, file_user_meta=user_meta_file
        )
        assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    else:
        md = SingleFileMetadataObject(
            f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}", True, file_user_meta=user_meta_file
        )
        assert md.file_object_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.SINGLE_FILE
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == "test-bucket/resourceid/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == "test-bucket/resourceid/.hsjsonld/has_parts.json"

    file_name = "testfile.txt"
    assert md.content_type_md_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"test-bucket/resourceid/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    assert md.content_type_md_user_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("use_folder", [True, False])
def test_singlefile(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "singlefile_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}testfile.txt.user_metadata.json", {
                  "user_metadata": "this is singlefile user metadata"})
    sleep(1)
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}testfile.txt")

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
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}testfile.txt.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}testfile.txt.json")
    assert len(result_metadata["associatedMedia"]) == 1
    assert result_metadata["associatedMedia"][
        0]["name"] == "testfile.txt"
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is singlefile user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_singlefile_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "singlefile_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}testfile.txt")

    sleep(1)
    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=0)
    result_has_parts = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert result_has_parts == []

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}testfile.txt.user_metadata.json", {
                  "user_metadata": "this is singlefile user metadata"})
    sleep(1)
    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}testfile.txt.json")
    singlefile_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}testfile.txt.json")
    assert singlefile_metadata["user_metadata"] == "this is singlefile user metadata"
    assert len(singlefile_metadata["associatedMedia"]) == 1
    assert singlefile_metadata["associatedMedia"][0]["name"] == "testfile.txt"
    assert len(singlefile_metadata["isPartOf"]) == 1
    assert singlefile_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
