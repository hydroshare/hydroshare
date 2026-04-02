import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json


def test_raster():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/raster_aggregation/logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan1.tif")

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
    assert result_has_parts[0]["url"].endswith("raster_aggregation/logan1.tif.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan1.tif.json")
    assert len(result_metadata["associatedMedia"]) == 1
    assert result_metadata["associatedMedia"][
        0]["name"] == "logan1.tif"
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is raster user metadata"


@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
def test_raster_usermetadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan1.tif")

    # Wait for metadata to be consistent
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan1.tif.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/raster_aggregation/logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan1.tif.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


def test_raster_vrt():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/raster_aggregation/logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan2.tif")

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
    assert result_has_parts[0]["url"].endswith("raster_aggregation/logan.vrt.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan.vrt.json")
    assert len(result_metadata["associatedMedia"]) == 3
    assert result_metadata["associatedMedia"][0]["name"] in ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
def test_raster_vrt_usermetadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/raster_aggregation/logan2.tif")

    # Wait for metadata to be consistent
    sleep(2)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan.vrt.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/raster_aggregation/logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)

    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan.vrt.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"
