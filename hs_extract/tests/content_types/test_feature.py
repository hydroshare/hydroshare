import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json
from hsextract.content_types.models import ContentType, BaseMetadataObject
from hsextract.content_types.feature.models import FeatureMetadataObject
from hsextract.content_types import determine_metadata_object_from_user_metadata


@pytest.mark.parametrize("shp_xml", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject(use_folder, shp_xml):
    folder_prefix = "test-folder/" if use_folder else ""
    res_bucket_path = "test-bucket/resourceid"
    file_name = "watersheds.shp"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    if shp_xml:
        file_name = "watersheds.shp.xml"

    md = FeatureMetadataObject(
        f"{res_bucket_path}/data/contents/{folder_prefix}{file_name}", True
    )
    file_name = "watersheds.shp"
    assert md.file_object_path == f"{res_bucket_path}/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == f"{res_bucket_path}/data/contents"
    assert md.resource_md_path == f"{res_bucket_path}/.hsmetadata"
    assert md.resource_md_jsonld_path == f"{res_bucket_path}/.hsjsonld"
    assert md.content_type == ContentType.FEATURE
    assert md.system_metadata_path == f"{res_bucket_path}/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == f"{res_bucket_path}/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == f"{res_bucket_path}/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == f"{res_bucket_path}/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == f"{res_bucket_path}/.hsjsonld/has_parts.json"
    assert md.content_type_md_jsonld_path == f"{res_bucket_path}/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"{res_bucket_path}/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"{res_bucket_path}/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"{res_bucket_path}/data/contents/{folder_prefix}{file_name}"
    assert md.content_type_md_user_path == f"{res_bucket_path}/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject_from_user_metadata(use_folder):
    resource_id = str(uuid.uuid4())
    folder_prefix = "test-folder/" if use_folder else ""
    file_name = "watersheds.shp"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    # upload the corresponding content file
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}{file_name}")
    # Wait for metadata to be consistent
    sleep(1)
    md = determine_metadata_object_from_user_metadata(
        f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}", True
    )
    assert isinstance(md, FeatureMetadataObject)
    assert md.file_object_path == f"test-bucket/{resource_id}/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == f"test-bucket/{resource_id}/data/contents"
    assert md.resource_md_path == f"test-bucket/{resource_id}/.hsmetadata"
    assert md.resource_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld"
    assert md.content_type == ContentType.FEATURE
    assert md.system_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/has_parts.json"
    assert md.content_type_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"test-bucket/{resource_id}/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"test-bucket/{resource_id}/data/contents/{folder_prefix}{file_name}"
    assert md.content_type_md_user_path == f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject_from_user_metadata_missing_content(use_folder):
    resource_id = str(uuid.uuid4())
    folder_prefix = "test-folder/" if use_folder else ""
    file_name = "watersheds.shp"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    md = determine_metadata_object_from_user_metadata(
        f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}", True
    )
    assert isinstance(md, BaseMetadataObject)
    assert not isinstance(md, FeatureMetadataObject)
    assert md.file_object_path == f"test-bucket/{resource_id}/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == f"test-bucket/{resource_id}/data/contents"
    assert md.resource_md_path == f"test-bucket/{resource_id}/.hsmetadata"
    assert md.resource_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld"
    assert md.content_type == ContentType.UNKNOWN
    assert md.system_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/has_parts.json"
    assert md.content_type_md_jsonld_path is None
    assert md.content_type_md_path is None
    assert md.content_type_contents_path is None
    assert md.content_type_main_file_path is None
    assert md.content_type_md_user_path is None
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("shp_xml", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
def test_feature_is_content_type(use_folder, shp_xml):
    resource_id = str(uuid.uuid4())
    folder_prefix = "feature_aggregation/" if use_folder else ""
    file_name = "watersheds.shp"
    if shp_xml:
        file_name = "watersheds.shp.xml"
    content_path = f"test-bucket/{resource_id}/data/contents/{folder_prefix}{file_name}"
    assert FeatureMetadataObject.is_content_type(content_path) is True


@pytest.mark.parametrize("use_folder", [True, False])
def test_feature(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "feature_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.shp")

    with open("tests/test_files/watersheds/watersheds.cpg", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.cpg")

    with open("tests/test_files/watersheds/watersheds.dbf", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.dbf")

    with open("tests/test_files/watersheds/watersheds.prj", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.prj")

    with open("tests/test_files/watersheds/watersheds.sbn", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.sbn")

    with open("tests/test_files/watersheds/watersheds.sbx", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.sbx")

    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.shx")

    with open("tests/test_files/watersheds/watersheds.shp.xml", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.shp.xml")

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
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}watersheds.shp.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}watersheds.shp.json")
    assert len(result_metadata["associatedMedia"]) == 8
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is feature user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_feature_user_metadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "feature_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/watersheds/watersheds.shp", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.shp")
    with open("tests/test_files/watersheds/watersheds.shx", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}watersheds.shx")

    sleep(2)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}watersheds.shp.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}watersheds.shp.user_metadata.json", {
                  "user_metadata": "this is feature user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}watersheds.shp.json")
    assert result_metadata["user_metadata"] == "this is feature user metadata"
