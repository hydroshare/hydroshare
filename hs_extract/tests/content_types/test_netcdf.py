import uuid

from time import sleep
from tests import s3_client, read_s3_json, write_s3_json


def test_resource_netcdf_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/netcdf_valid.nc.user_metadata.json", {
                  "user_metadata": "this is netcdf user metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json", {
                  "system_metadata": "this is system metadata"})
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {
                  "user_metadata": "this is user metadata"})

    with open("tests/test_files/netcdf/netcdf_valid.nc", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/netcdf_valid.nc")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("netcdf_valid.nc.json")

    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/netcdf_valid.nc.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "netcdf_valid.nc"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0].endswith("dataset_metadata.json")
    assert result_netcdf_metadata[
        "user_metadata"] == "this is netcdf user metadata"


def test_resource_netcdf_user_metadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID

    with open("tests/test_files/netcdf/netcdf_valid.nc", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/netcdf_valid.nc")

    # Wait for metadata to be consistent
    sleep(1)
    result_netcdf_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/netcdf_valid.nc.json")
    assert "user_metadata" not in result_netcdf_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", {"user_metadata": "this is user metadata"})
    sleep(1)
    assert result_netcdf_metadata["user_metadata"] == "this is netcdf user metadata"
