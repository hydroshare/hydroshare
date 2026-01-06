import os
import sys
import uuid
from pathlib import Path
from time import sleep

import pytest

from tests import read_s3_json, s3_client, write_s3_json

# Stub optional heavy deps referenced by content type modules
sys.modules.setdefault("rasterio", None)
sys.modules.setdefault("xarray", None)
sys.modules.setdefault("geopandas", None)

from hsextract.content_types.models import BaseMetadataObject, FileMetadataObject
from hsextract.main import write_content_type_jsonld_metadata, write_resource_jsonld_metadata


TEST_FILES_DIR = Path("tests/test_files/timeseries")
CSV_FIXTURE = TEST_FILES_DIR / "ODM2_Multi_Site_One_Variable_Test.csv"
SQLITE_FIXTURE = TEST_FILES_DIR / "ODM2_Multi_Site_One_Variable.sqlite"


def _haspart_urls(has_part):
    urls = set()
    for part in has_part or []:
        if isinstance(part, dict):
            if part.get("url"):
                urls.add(part["url"])
            elif isinstance(part.get("identifier"), str):
                urls.add(part["identifier"])
            elif isinstance(part.get("identifier"), list) and part["identifier"]:
                urls.add(part["identifier"][0])
    return urls


def test_resource_haspart_merges_user_and_extracted():
    resource_id = str(uuid.uuid4())
    bucket = "test-bucket"
    resource_prefix = f"{bucket}/{resource_id}"

    extracted_part_url = f"{os.environ.get('AWS_S3_ENDPOINT_URL', 'http://minio:9000')}/{resource_prefix}/.hsjsonld/dummy.csv.json"
    write_s3_json(
        f"{resource_prefix}/.hsjsonld/dummy.csv.json",
        {"name": "dummy", "hasPart": [], "isPartOf": []},
    )

    user_parts = [
        {"url": extracted_part_url},
        {"url": "https://example.com/user-only-part-1"},
        {"url": "https://example.com/user-only-part-2"},
    ]
    write_s3_json(f"{resource_prefix}/.hsmetadata/user_metadata.json", {"hasPart": user_parts})

    md = BaseMetadataObject(f"{resource_prefix}/.hsmetadata/user_metadata.json", True)
    write_resource_jsonld_metadata(md)

    result = read_s3_json(f"{resource_prefix}/.hsjsonld/dataset_metadata.json")
    urls = _haspart_urls(result.get("hasPart"))

    assert len(result["hasPart"]) == 4
    assert urls == {
        extracted_part_url,
        "https://example.com/user-only-part-1",
        "https://example.com/user-only-part-2",
    }


def test_content_type_haspart_merges_user_and_extracted():
    resource_id = str(uuid.uuid4())
    bucket = "test-bucket"
    resource_prefix = f"{bucket}/{resource_id}"
    file_name = "ODM2_Multi_Site_One_Variable_Test.csv"
    file_path = f"{resource_prefix}/data/contents/{file_name}"

    content_part_url = f"{os.environ.get('AWS_S3_ENDPOINT_URL', 'http://minio:9000')}/{resource_prefix}/.hsjsonld/{file_name}.json"
    write_s3_json(
        f"{resource_prefix}/.hsmetadata/{file_name}.json",
        {"name": file_name, "hasPart": [{"url": content_part_url}]},
    )
    write_s3_json(
        f"{resource_prefix}/.hsmetadata/{file_name}.user_metadata.json",
        {"hasPart": [{"identifier": [content_part_url]}, {"url": "https://example.com/user-extra"}]},
    )

    md = FileMetadataObject(file_path, True)
    write_content_type_jsonld_metadata(md)

    result = read_s3_json(f"{resource_prefix}/.hsjsonld/{file_name}.json")
    urls = _haspart_urls(result.get("hasPart"))

    assert len(result["hasPart"]) == 3
    assert content_part_url in urls
    assert "https://example.com/user-extra" in urls


def test_resource_haspart_user_only_when_no_extracted_parts():
    resource_id = str(uuid.uuid4())
    bucket = "test-bucket"
    resource_prefix = f"{bucket}/{resource_id}"

    user_parts = [
        {"url": "https://example.com/user-only-part-1"},
        {"url": "https://example.com/user-only-part-2"},
    ]
    write_s3_json(f"{resource_prefix}/.hsmetadata/user_metadata.json", {"hasPart": user_parts})

    md = BaseMetadataObject(f"{resource_prefix}/.hsmetadata/user_metadata.json", True)
    write_resource_jsonld_metadata(md)

    for _ in range(5):
        result = read_s3_json(f"{resource_prefix}/.hsjsonld/dataset_metadata.json")
        if result.get("hasPart"):
            break
        sleep(0.2)
    urls = _haspart_urls(result.get("hasPart"))

    assert len(result["hasPart"]) == 2
    assert urls == {"https://example.com/user-only-part-1", "https://example.com/user-only-part-2"}


def test_resource_timeseries_csv_extraction():
    if not CSV_FIXTURE.exists():
        pytest.skip("CSV fixture missing")
    resource_id = str(uuid.uuid4())
    write_s3_json(
        f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable_Test.csv.user_metadata.json",
        {"user_metadata": "this is timeseries user metadata"},
    )
    with open(CSV_FIXTURE, "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{CSV_FIXTURE.name}")

    sleep(1)
    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert len(result_resource_metadata["associatedMedia"]) == 1
    assert result_resource_metadata["associatedMedia"][0]["name"] == CSV_FIXTURE.name
    assert len(result_resource_metadata["hasPart"]) == 1
    assert result_resource_metadata["hasPart"][0]["url"].endswith(f"{CSV_FIXTURE.name}.json")

    result_timeseries_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{CSV_FIXTURE.name}.json"
    )
    assert len(result_timeseries_metadata["associatedMedia"]) == 1
    assert result_timeseries_metadata["associatedMedia"][0]["name"] == CSV_FIXTURE.name
    assert len(result_timeseries_metadata["isPartOf"]) == 1
    assert result_timeseries_metadata["isPartOf"][0].endswith("dataset_metadata.json")
    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"


+@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
+def test_resource_timeseries_csv_usermetadata():
+    resource_id = str(uuid.uuid4())
+    with open(CSV_FIXTURE, "rb") as f:
+        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{CSV_FIXTURE.name}")
+    sleep(1)
+    result_timeseries_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{CSV_FIXTURE.name}.json")
+    assert "user_metadata" not in result_timeseries_metadata
+    write_s3_json(
+        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json",
+        {"user_metadata": "this is user metadata"},
+    )
+    sleep(1)
+    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"
+
+
+def test_resource_timeseries_sqlite_extraction():
+    if not SQLITE_FIXTURE.exists():
+        pytest.skip("SQLite fixture missing")
+    resource_id = str(uuid.uuid4())
+    write_s3_json(
+        f"test-bucket/{resource_id}/.hsmetadata/ODM2_Multi_Site_One_Variable.sqlite.user_metadata.json",
+        {"user_metadata": "this is timeseries user metadata"},
+    )
+    with open(SQLITE_FIXTURE, "rb") as f:
+        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{SQLITE_FIXTURE.name}")
+
+    sleep(1)
+    result_resource_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")
+
+    assert len(result_resource_metadata["associatedMedia"]) == 1
+    assert result_resource_metadata["associatedMedia"][0]["name"] == SQLITE_FIXTURE.name
+    assert len(result_resource_metadata["hasPart"]) == 1
+    assert result_resource_metadata["hasPart"][0]["url"].endswith(f"{SQLITE_FIXTURE.name}.json")
+
+    result_timeseries_metadata = read_s3_json(
+        f"test-bucket/{resource_id}/.hsjsonld/{SQLITE_FIXTURE.name}.json"
+    )
+    assert len(result_timeseries_metadata["associatedMedia"]) == 1
+    assert result_timeseries_metadata["associatedMedia"][0]["name"] == SQLITE_FIXTURE.name
+    assert len(result_timeseries_metadata["isPartOf"]) == 1
+    assert result_timeseries_metadata["isPartOf"][0].endswith("dataset_metadata.json")
+    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"
+
+
+@pytest.mark.skip(reason="User metadata event update for content types is not currently implemented")
+def test_resource_timeseries_sqlite_usermetadata():
+    resource_id = str(uuid.uuid4())
+    with open(SQLITE_FIXTURE, "rb") as f:
+        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{SQLITE_FIXTURE.name}")
+    sleep(1)
+    result_timeseries_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{SQLITE_FIXTURE.name}.json")
+    assert "user_metadata" not in result_timeseries_metadata
+    write_s3_json(
+        f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json",
+        {"user_metadata": "this is user metadata"},
+    )
+    sleep(1)
+    assert result_timeseries_metadata["user_metadata"] == "this is timeseries user metadata"
+
