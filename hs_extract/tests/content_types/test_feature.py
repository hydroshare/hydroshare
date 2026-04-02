import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json


def test_feature():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/feature_aggregation/watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp")

    with open("tests/test_files/watersheds/watersheds.cpg", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.cpg")

    with open("tests/test_files/watersheds/watersheds.dbf", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.dbf")

    with open("tests/test_files/watersheds/watersheds.prj", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.prj")

    with open("tests/test_files/watersheds/watersheds.sbn", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.sbn")

    with open("tests/test_files/watersheds/watersheds.sbx", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.sbx")

    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.shx")

    with open("tests/test_files/watersheds/watersheds.shp.xml", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp.xml")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=8)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith("feature_aggregation/watersheds.shp.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert len(result_metadata["associatedMedia"]) == 8
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is feature user metadata"


@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
def test_feature_user_metadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.shp")
    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/feature_aggregation/watersheds.shx")

    sleep(2)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/feature_aggregation/watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/feature_aggregation/watersheds.shp.json")
    assert result_metadata["user_metadata"] == "this is feature user metadata"
