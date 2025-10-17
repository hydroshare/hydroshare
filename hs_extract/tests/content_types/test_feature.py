import uuid

from time import sleep
from tests import s3_client, read_s3_json, write_s3_json


def test_feature():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    logging.info(resource_id)
    write_s3_json(f"admin/{resource_id}/.hsmetadata/feature_aggregation/watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp")

    with open("tests/test_files/watersheds/watersheds.cpg", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.cpg")

    with open("tests/test_files/watersheds/watersheds.dbf", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.dbf")

    with open("tests/test_files/watersheds/watersheds.prj", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.prj")

    with open("tests/test_files/watersheds/watersheds.sbn", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.sbn")

    with open("tests/test_files/watersheds/watersheds.sbx", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.sbx")

    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.shx")

    with open("tests/test_files/watersheds/watersheds.shp.xml", "rb") as f:
        s3_client.upload_fileobj(
            f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp.xml")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"admin/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 8
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][
        0]["url"].endswith("feature_aggregation/watersheds.shp.json")

    result_metadata = read_s3_json(
        f"admin/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert len(result_metadata["associatedMedia"]) == 8
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is feature user metadata"


def test_feature_user_metadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp")
    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(f, "admin", f"{resource_id}/data/contents/feature_aggregation/watersheds.shx")

    sleep(2)
    result_metadata = read_s3_json(f"admin/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"admin/{resource_id}/.hsmetadata/feature_aggregation/watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"admin/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert result_metadata["user_metadata"] == "this is feature user metadata"
