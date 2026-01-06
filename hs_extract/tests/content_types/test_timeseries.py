import os
import sys
import types
import uuid
from pathlib import Path
from time import sleep

import pytest
from tests import read_s3_json, s3_client, write_s3_json

# Stub heavy deps so test collection doesn’t require rasterio/xarray/geopandas.
sys.modules.setdefault("rasterio", types.SimpleNamespace(open=lambda *_, **__: None))
sys.modules.setdefault("xarray", types.SimpleNamespace(Dataset=object))
sys.modules.setdefault("geopandas", types.SimpleNamespace(read_file=lambda *_, **__: None))

from hsextract.content_types.models import BaseMetadataObject, FileMetadataObject
from hsextract.main import write_content_type_jsonld_metadata, write_resource_jsonld_metadata

TEST_FILES_DIR = Path(__file__).resolve().parents[2] / "test_files" / "timeseries"
CSV_FIXTURE = TEST_FILES_DIR / "ODM2_Multi_Site_One_Variable_Test.csv"
SQLITE_FIXTURE = TEST_FILES_DIR / "ODM2_Multi_Site_One_Variable.sqlite"


def test_resource_haspart_merges_user_and_extracted():
    resource_id = str(uuid.uuid4())
    endpoint = os.environ.get("AWS_S3_ENDPOINT_URL", "http://minio:9000")

    # Simulate an extracted content-type JSON-LD file
    extracted_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/sample_part.json"
    write_s3_json(extracted_metadata_path, {"name": "extracted"})
    extracted_part_url = f"{endpoint}/{extracted_metadata_path}"

    user_parts = [
        {"name": "duplicate extracted part", "url": extracted_part_url},
        {"name": "external reference 1", "url": "https://example.com/user-haspart-1"},
        {"name": "external reference 2", "url": "https://example.com/user-haspart-2"},
    ]
    write_s3_json(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json",
        {"hasPart": user_parts},
    )

    md = BaseMetadataObject(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", True
    )
    write_resource_jsonld_metadata(md)
    sleep(0.5)

    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    )
    has_part_urls = [part["url"] for part in result_resource_metadata["hasPart"]]

    # extracted + 3 user entries (one duplicate of extracted) = 4 entries (joined)
    assert len(result_resource_metadata["hasPart"]) == 4
    assert has_part_urls.count(extracted_part_url) == 2
    assert "https://example.com/user-haspart-1" in has_part_urls
    assert "https://example.com/user-haspart-2" in has_part_urls


def test_content_type_haspart_merges_user_and_extracted():
    resource_id = str(uuid.uuid4())
    file_name = "ODM2_Multi_Site_One_Variable_Test.csv"
    object_path = f"test-bucket/{resource_id}/data/contents/{file_name}"
    md = FileMetadataObject(object_path, True)

    content_part_url = "https://example.com/content-type-part"
    user_part_url = "https://example.com/user-part"

    write_s3_json(md.content_type_md_path, {"hasPart": [{"url": content_part_url}]})
    write_s3_json(
        md.content_type_md_user_path,
        {
            "hasPart": [
                {"identifier": [content_part_url]},  # duplicate via identifier list
                {"url": user_part_url},
            ]
        },
    )

    write_content_type_jsonld_metadata(md)

    result_metadata = read_s3_json(md.content_type_md_jsonld_path)
    has_part_urls = [part.get("url") or part.get("identifier") for part in result_metadata["hasPart"]]

    # content hasPart + user duplicate via identifier + user new = 3 entries (joined)
    assert len(result_metadata["hasPart"]) == 3
    assert content_part_url in has_part_urls
    assert user_part_url in has_part_urls


def test_resource_haspart_user_only_when_no_extracted_parts():
    resource_id = str(uuid.uuid4())
    user_parts = [
        {"url": "https://example.com/user-only-part-1"},
        {"url": "https://example.com/user-only-part-2"},
    ]
    write_s3_json(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json",
        {"hasPart": user_parts},
    )

    md = BaseMetadataObject(
        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json", True
    )
    write_resource_jsonld_metadata(md)

    result_resource_metadata = {}
    for _ in range(5):
        result_resource_metadata = read_s3_json(
            f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
        )
        if result_resource_metadata.get("hasPart"):
            break
        sleep(0.2)
    has_part_urls = {part["url"] for part in result_resource_metadata["hasPart"]}

    assert len(result_resource_metadata["hasPart"]) == 2
    assert "https://example.com/user-only-part-1" in has_part_urls
    assert "https://example.com/user-only-part-2" in has_part_urls


def test_resource_timeseries_csv_extraction():
    if not CSV_FIXTURE.exists():
        pytest.skip("CSV fixture not available")
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open(CSV_FIXTURE, "rb") as f:
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


@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
def test_resource_timeseries_csv_usermetadata():
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    sleep(1)
    with open("tests/test_files/timeseries/ODM2_Multi_Site_One_Variable_Test.csv", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/ODM2_Multi_Site_One_Variable_Test.csv")

    result_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable_Test.csv.json"
    result_netcdf_metadata = read_s3_json(result_metadata_path)
    assert "user_metadata" not in result_netcdf_metadata
    sleep(1)

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    result_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/ODM2_Multi_Site_One_Variable_Test.csv.json"
    result_netcdf_metadata = read_s3_json(result_metadata_path)
    assert result_netcdf_metadata["user_metadata"] == "this is timeseries user metadata"


def test_resource_timeseries_sqlite_extraction():
    if not SQLITE_FIXTURE.exists():
        pytest.skip("SQLite fixture not available")
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable.sqlite.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open(SQLITE_FIXTURE, "rb") as f:
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


@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
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
