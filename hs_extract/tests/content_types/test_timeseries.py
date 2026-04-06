import os
import sys
import types
import uuid
from pathlib import Path
from time import sleep
import pytest

from hsextract.content_types.models import BaseMetadataObject, FileMetadataObject, ContentType
from hsextract.content_types.timeseries.models import TimeSeriesMetadataObject
from hsextract.main import write_content_type_jsonld_metadata, write_resource_jsonld_metadata
from tests import assert_has_part_reference, assert_manifest_reference, read_s3_json, s3_client, write_s3_json

# Stub heavy deps so test collection doesn’t require rasterio/xarray/geopandas.
sys.modules.setdefault("rasterio", types.SimpleNamespace(open=lambda *_, **__: None))
sys.modules.setdefault("xarray", types.SimpleNamespace(Dataset=object))
sys.modules.setdefault("geopandas", types.SimpleNamespace(read_file=lambda *_, **__: None))

TEST_FILES_DIR = Path(__file__).resolve().parents[1] / "test_files" / "timeseries"
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
    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=0)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=4)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json"
    )
    has_part_urls = [part["url"] for part in result_has_parts]

    # extracted + 3 user entries (one duplicate of extracted) = 4 entries (joined)
    assert len(result_has_parts) == 4
    assert has_part_urls.count(extracted_part_url) == 2
    assert "https://example.com/user-haspart-1" in has_part_urls
    assert "https://example.com/user-haspart-2" in has_part_urls


def test_content_type_haspart_merges_user_and_extracted():
    resource_id = str(uuid.uuid4())
    file_name = "ODM2_Multi_Site_One_Variable_Test.csv"
    object_path = f"test-bucket/{resource_id}/data/contents/{file_name}"
    md = FileMetadataObject(object_path, file_updated=True, file_user_meta=False)

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
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=2)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json"
    )
    has_part_urls = {part["url"] for part in result_has_parts}

    assert len(result_has_parts) == 2
    assert "https://example.com/user-only-part-1" in has_part_urls
    assert "https://example.com/user-only-part-2" in has_part_urls


@pytest.mark.parametrize("user_meta_file", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
@pytest.mark.parametrize("use_sqlite", [True, False])
def test_metadataobject(use_folder, use_sqlite, user_meta_file):
    folder_prefix = "test-folder/" if use_folder else ""
    base_file_name = "ODM2_Multi_Site_One_Variable.sqlite" if use_sqlite else "ODM2_Multi_Site_One_Variable_Test.csv"
    if not user_meta_file:
        file_name = base_file_name
        user_meta_file_name = f"{file_name}.user_metadata.json"
    else:
        file_name = f"{base_file_name}.user_metadata.json"
        user_meta_file_name = file_name

    if not user_meta_file:
        md = TimeSeriesMetadataObject(
            f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}", True, file_user_meta=user_meta_file
        )
        assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    else:
        md = TimeSeriesMetadataObject(
            f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}", True, file_user_meta=user_meta_file
        )
        assert md.file_object_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.TIMESERIES
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == "test-bucket/resourceid/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == "test-bucket/resourceid/.hsjsonld/has_parts.json"

    file_name = base_file_name
    assert md.content_type_md_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"test-bucket/resourceid/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    assert md.content_type_md_user_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("metadata_exists", [True, False])
@pytest.mark.parametrize("user_meta_file", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
@pytest.mark.parametrize("use_sqlite", [True, False])
def test_timeseries_is_content_type(use_folder, use_sqlite, user_meta_file, metadata_exists):
    resource_id = str(uuid.uuid4())
    folder_prefix = "timeseries_aggregation/" if use_folder else ""
    base_file_name = "ODM2_Multi_Site_One_Variable.sqlite" if use_sqlite else "ODM2_Multi_Site_One_Variable_Test.csv"
    content_path = f"test-bucket/{resource_id}/data/contents/{folder_prefix}{base_file_name}"
    user_metadata_path = f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{base_file_name}.user_metadata.json"

    if metadata_exists:
        write_s3_json(user_metadata_path, {"user_metadata": "this is timeseries user metadata"})
        sleep(1)

    file_object_path = user_metadata_path if user_meta_file else content_path
    expected = metadata_exists if user_meta_file else True

    assert TimeSeriesMetadataObject.is_content_type(file_object_path) is expected


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_timeseries_csv_extraction(use_folder):
    if not CSV_FIXTURE.exists():
        pytest.fail("CSV fixture not available")
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "timeseries_aggregation/" if use_folder else ""
    print(resource_id)
    user_meta_file_name = "ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json"
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open(CSV_FIXTURE, "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}ODM2_Multi_Site_One_Variable_Test.csv")

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
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}ODM2_Multi_Site_One_Variable_Test.csv.json")

    result_timeseries_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}ODM2_Multi_Site_One_Variable_Test.csv.json")
    assert len(result_timeseries_metadata["associatedMedia"]) == 1
    assert result_timeseries_metadata["associatedMedia"][
        0]["name"] == "ODM2_Multi_Site_One_Variable_Test.csv"
    assert len(result_timeseries_metadata["isPartOf"]) == 1
    assert result_timeseries_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_timeseries_metadata[
        "user_metadata"] == "this is timeseries user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_timeseries_csv_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    csv_file_name = "ODM2_Multi_Site_One_Variable_Test.csv"
    folder_prefix = "timeseries_aggregation/" if use_folder else ""
    with open(f"tests/test_files/timeseries/{csv_file_name}", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}{csv_file_name}")

    sleep(1)
    result_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{csv_file_name}.json"
    result_timeseries_metadata = read_s3_json(result_metadata_path)
    assert "user_metadata" not in result_timeseries_metadata
    sleep(1)

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{csv_file_name}.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    result_metadata_path = f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{csv_file_name}.json"
    result_timeseries_metadata = read_s3_json(result_metadata_path)
    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_timeseries_sqlite_extraction(use_folder):
    if not SQLITE_FIXTURE.exists():
        pytest.skip("SQLite fixture not available")
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "timeseries_aggregation/" if use_folder else ""
    sqlite_file_name = "ODM2_Multi_Site_One_Variable.sqlite"
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{sqlite_file_name}.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    with open(SQLITE_FIXTURE, "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}{sqlite_file_name}")

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
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}{sqlite_file_name}.json")

    result_timeseries_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{sqlite_file_name}.json")
    assert len(result_timeseries_metadata["associatedMedia"]) == 1
    assert result_timeseries_metadata["associatedMedia"][
        0]["name"] == sqlite_file_name
    assert len(result_timeseries_metadata["isPartOf"]) == 1
    assert result_timeseries_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_resource_timeseries_sqlite_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "timeseries_aggregation/" if use_folder else ""
    sqlite_file_name = "ODM2_Multi_Site_One_Variable.sqlite"
    with open(f"tests/test_files/timeseries/{sqlite_file_name}", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}{sqlite_file_name}")
    sleep(1)

    result_timeseries_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{sqlite_file_name}.json")
    assert "user_metadata" not in result_timeseries_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{sqlite_file_name}.user_metadata.json", {
                  "user_metadata": "this is timeseries user metadata"})
    sleep(1)
    result_timeseries_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{sqlite_file_name}.json")
    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"
