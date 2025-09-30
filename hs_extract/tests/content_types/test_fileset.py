from time import sleep

import uuid
from tests import s3_client, read_s3_json, write_s3_json


def test_fileset():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"admin/{resource_id}/.hsmetadata/folder_aggregation/user_metadata.json", {
                  "user_metadata": "this is fileset user metadata"})
    sleep(1)
    with open("tests/test_files/folder_aggregation/testfile.txt", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/folder_aggregation/testfile.txt")

    # Wait for metadata to be consistent
    sleep(1)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"admin/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == "testfile.txt"
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][0]["url"].endswith("folder_aggregation/dataset_metadata.json")

    result_netcdf_metadata = read_s3_json(
        f"admin/{resource_id}/.hsjsonld/folder_aggregation/dataset_metadata.json")
    assert len(result_netcdf_metadata["associatedMedia"]) == 1
    assert result_netcdf_metadata["associatedMedia"][0]["name"] == "testfile.txt"
    assert len(result_netcdf_metadata["isPartOf"]) == 1
    assert result_netcdf_metadata["isPartOf"][0].endswith("dataset_metadata.json")
    assert result_netcdf_metadata["user_metadata"] == "this is fileset user metadata"
