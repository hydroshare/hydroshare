import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}logan1.tif.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert len(result_metadata["associatedMedia"]) == 1
    assert result_metadata["associatedMedia"][
        0]["name"] == "logan1.tif"
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")

    # Wait for metadata to be consistent
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_vrt(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan2.tif")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=3)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}logan.vrt.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert len(result_metadata["associatedMedia"]) == 3
    assert result_metadata["associatedMedia"][0]["name"] in ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_vrt_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan2.tif")

    # Wait for metadata to be consistent
    sleep(2)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)

    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"
