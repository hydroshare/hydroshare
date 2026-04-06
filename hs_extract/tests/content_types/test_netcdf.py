import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json
from hsextract.content_types.models import ContentType
from hsextract.content_types.netcdf.models import NetCDFMetadataObject


@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject(use_folder):
    folder_prefix = "test-folder/" if use_folder else ""
    file_name = "netcdf_valid.nc"
    md = NetCDFMetadataObject(f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}", True)
    assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.NETCDF
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == "test-bucket/resourceid/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == "test-bucket/resourceid/.hsjsonld/has_parts.json"

    assert md.content_type_md_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"test-bucket/resourceid/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    assert md.content_type_md_user_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_netcdf_extraction(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "netcdf_aggr/" if use_folder else ""
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}netcdf_valid.nc.user_metadata.json", {
                  "user_metadata": "this is netcdf user metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    with open("tests/test_files/netcdf/netcdf_valid.nc", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}netcdf_valid.nc")

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
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}netcdf_valid.nc.json")

    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}netcdf_valid.nc.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_netcdf_metadata[
        "user_metadata"] == "this is netcdf user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_netcdf_user_metadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "netcdf_aggr/" if use_folder else ""

    with open("tests/test_files/netcdf/netcdf_valid.nc", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}netcdf_valid.nc")

    # Wait for metadata to be consistent
    sleep(1)
    resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
    # check has part and manifest reference is correct before user metadata update
    assert_manifest_reference(resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)

    result_netcdf_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}netcdf_valid.nc.json")
    assert "user_metadata" not in result_netcdf_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}netcdf_valid.nc.user_metadata.json",
                  {"user_metadata": "this is netcdf user metadata"})
    sleep(1)
    result_netcdf_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}netcdf_valid.nc.json")
    assert result_netcdf_metadata["user_metadata"] == "this is netcdf user metadata"
    # check associated media is still correct
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
