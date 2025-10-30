import uuid

from time import sleep
from tests import s3_client, read_s3_json, write_s3_json


def test_resource_timeseries_csv_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open("tests/test_files/timeseries/ODM2_Multi_Site_One_Variable_Test.csv", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/ODM2_Multi_Site_One_Variable_Test.csv")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][
        0]["name"] == "ODM2_Multi_Site_One_Variable_Test.csv"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("ODM2_Multi_Site_One_Variable_Test.csv.json")

    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable_Test.csv.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "ODM2_Multi_Site_One_Variable_Test.csv"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0].endswith("dataset_metadata.json")
    assert result_netcdf_metadata[
        "user_metadata"] == "this is timeseries user metadata"


def test_resource_timeseries_csv_usermetadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    sleep(1)
    with open("tests/test_files/timeseries/ODM2_Multi_Site_One_Variable_Test.csv", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/ODM2_Multi_Site_One_Variable_Test.csv")

    result_netcdf_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable_Test.csv.json")
    assert "user_metadata" not in result_netcdf_metadata
    sleep(1)

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    result_netcdf_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable_Test.csv.json")
    assert result_netcdf_metadata["user_metadata"] == "this is timeseries user metadata"


def test_resource_timeseries_sqlite_extraction():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable.sqlite.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open("tests/test_files/timeseries/ODM2_Multi_Site_One_Variable.sqlite", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/ODM2_Multi_Site_One_Variable.sqlite")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][
        0]["name"] == "ODM2_Multi_Site_One_Variable.sqlite"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("ODM2_Multi_Site_One_Variable.sqlite.json")

    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable.sqlite.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][
        0]["name"] == "ODM2_Multi_Site_One_Variable.sqlite"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][
        0].endswith("dataset_metadata.json")
    assert result_netcdf_metadata["user_metadata"] == "this is timeseries user metadata"


def test_resource_timeseries_sqlite_usermetadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    with open("tests/test_files/timeseries/ODM2_Multi_Site_One_Variable.sqlite", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/ODM2_Multi_Site_One_Variable.sqlite")
    sleep(1)

    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable.sqlite.json")
    assert "user_metadata" not in result_netcdf_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable.sqlite.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    result_netcdf_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable.sqlite.json")
    assert result_netcdf_metadata["user_metadata"] == "this is timeseries user metadata"
