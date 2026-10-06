import uuid

from hsextract.content_types.models import FileMetadataObject
from hsextract.main import write_content_type_jsonld_metadata, write_resource_jsonld_metadata
from tests import assert_has_part_reference, read_s3_json, s3_path_exists, write_s3_json


def _make_file_metadata_object(file_name: str = "sample.txt") -> FileMetadataObject:
    resource_id = str(uuid.uuid4())
    object_path = f"test-bucket/{resource_id}/data/contents/{file_name}"
    return FileMetadataObject(object_path, file_updated=True)


def test_deletes_stale_jsonld_when_no_content_type_or_user_metadata():
    md = _make_file_metadata_object()
    # Simulate a jsonld file left over from a previous extraction that no
    # longer has any backing content-type or user metadata.
    write_s3_json(md.content_type_md_jsonld_path, {"name": "stale"})
    assert s3_path_exists(md.content_type_md_jsonld_path) is True
    assert s3_path_exists(md.content_type_md_path) is False
    assert s3_path_exists(md.content_type_md_user_path) is False

    write_content_type_jsonld_metadata(md)

    assert s3_path_exists(md.content_type_md_jsonld_path) is False


def test_noop_when_no_metadata_and_no_existing_jsonld_file():
    md = _make_file_metadata_object()
    assert s3_path_exists(md.content_type_md_jsonld_path) is False

    # Should not raise even though there is nothing to delete.
    write_content_type_jsonld_metadata(md)

    assert s3_path_exists(md.content_type_md_jsonld_path) is False


def test_writes_jsonld_when_content_type_metadata_present():
    md = _make_file_metadata_object()
    write_s3_json(md.content_type_md_path, {"name": "sample"})

    write_content_type_jsonld_metadata(md)
    assert s3_path_exists(md.content_type_md_jsonld_path) is True
    assert s3_path_exists(md.content_type_md_path) is True
    assert s3_path_exists(md.content_type_md_user_path) is False

    result = read_s3_json(md.content_type_md_jsonld_path)
    assert result["name"] == "sample"
    assert len(result["isPartOf"]) == 1
    assert result["isPartOf"][0]["url"].endswith("dataset_metadata.json")


def test_writes_jsonld_when_only_user_metadata_present():
    md = _make_file_metadata_object()
    write_s3_json(md.content_type_md_user_path, {"name": "user supplied"})

    write_content_type_jsonld_metadata(md)
    assert s3_path_exists(md.content_type_md_jsonld_path) is True
    assert s3_path_exists(md.content_type_md_path) is False
    assert s3_path_exists(md.content_type_md_user_path) is True

    result = read_s3_json(md.content_type_md_jsonld_path)
    assert result["name"] == "user supplied"
    assert len(result["isPartOf"]) == 1
    assert result["isPartOf"][0]["url"].endswith("dataset_metadata.json")


def test_resource_has_part_empty_when_no_content_type_jsonld():
    md = _make_file_metadata_object()
    assert s3_path_exists(md.content_type_md_jsonld_path) is False

    write_resource_jsonld_metadata(md)

    result = read_s3_json(md.resource_metadata_jsonld_path)
    assert_has_part_reference(result, md.resource_id, "test-bucket", expected_has_part_count=0)


def test_writes_jsonld_when_both_content_type_and_user_metadata_present():
    md = _make_file_metadata_object()
    write_s3_json(md.content_type_md_path, {"name": "sample"})
    write_s3_json(md.content_type_md_user_path, {"description": "user supplied"})

    write_content_type_jsonld_metadata(md)
    assert s3_path_exists(md.content_type_md_jsonld_path) is True
    assert s3_path_exists(md.content_type_md_path) is True
    assert s3_path_exists(md.content_type_md_user_path) is True

    result = read_s3_json(md.content_type_md_jsonld_path)
    assert result["name"] == "sample"
    assert result["description"] == "user supplied"
    assert len(result["isPartOf"]) == 1
    assert result["isPartOf"][0]["url"].endswith("dataset_metadata.json")
