import uuid
import pytest

from time import sleep
from tests import s3_client, read_s3_json, write_s3_json


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

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][
        0]["name"] == "logan1.tif"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("raster_aggregation/logan1.tif.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan1.tif.json")
    assert len(result_metadata["associatedMedia"]) == 1
    assert result_metadata["associatedMedia"][
        0]["name"] == "logan1.tif"
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][
        0].endswith("dataset_metadata.json")
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

    assert len(result_resource_metadata["associatedMedia"]) == 3
    assert result_resource_metadata["associatedMedia"][0]["name"] in ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][0]["url"].endswith("raster_aggregation/logan.vrt.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/raster_aggregation/logan.vrt.json")
    assert len(result_metadata["associatedMedia"]) == 3
    assert result_metadata["associatedMedia"][0]["name"] in ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0].endswith("dataset_metadata.json")
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
