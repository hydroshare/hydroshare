import uuid
import pytest

from time import sleep
from tests import assert_has_part_reference, assert_manifest_reference, s3_client, read_s3_json, write_s3_json
from hsextract.content_types.models import BaseMetadataObject, ContentType
from hsextract.content_types.raster.models import RasterMetadataObject
from hsextract.content_types import determine_metadata_object_from_user_metadata


@pytest.mark.parametrize("use_folder", [True, False])
@pytest.mark.parametrize("use_vrt", [True, False])
def test_metadataobject(use_folder, use_vrt):
    folder_prefix = "test-folder/" if use_folder else ""
    file_name = "logan.vrt" if use_vrt else "logan1.tif"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    md = RasterMetadataObject(
        f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}", True
    )
    assert md.file_object_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == "test-bucket/resourceid/data/contents"
    assert md.resource_md_path == "test-bucket/resourceid/.hsmetadata"
    assert md.resource_md_jsonld_path == "test-bucket/resourceid/.hsjsonld"
    assert md.content_type == ContentType.RASTER
    assert md.system_metadata_path == "test-bucket/resourceid/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == "test-bucket/resourceid/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == "test-bucket/resourceid/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == "test-bucket/resourceid/.hsjsonld/file_manifest.json"
    assert md.resource_has_parts_jsonld_path == "test-bucket/resourceid/.hsjsonld/has_parts.json"
    assert md.content_type_md_jsonld_path == f"test-bucket/resourceid/.hsjsonld/{folder_prefix}{file_name}.json"
    assert md.content_type_md_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{file_name}.json"
    assert md.content_type_contents_path == f"test-bucket/resourceid/data/contents/{folder_prefix.rstrip('/')}"
    assert md.content_type_main_file_path == f"test-bucket/resourceid/data/contents/{folder_prefix}{file_name}"
    assert md.content_type_md_user_path == f"test-bucket/resourceid/.hsmetadata/{folder_prefix}{user_meta_file_name}"
    assert md._content_type_associated_media is None


@pytest.mark.parametrize("use_vrt", [True, False])
@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject_from_user_metadata(use_folder, use_vrt):
    resource_id = str(uuid.uuid4())
    folder_prefix = "test-folder/" if use_folder else ""
    if use_vrt:
        file_name = "logan.vrt"
    else:
        file_name = "logan1.tif"

    user_meta_file_name = f"{file_name}.user_metadata.json"
    # upload a taster data file
    if use_vrt:
        with open("tests/test_files/rasters/logan.vrt", "rb") as f:
            s3_client.upload_fileobj(
                f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan.vrt")
    else:
        with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
            s3_client.upload_fileobj(
                f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")
    sleep(1)
    md = determine_metadata_object_from_user_metadata(
        f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}", True
    )
    assert isinstance(md, RasterMetadataObject)
    assert md.file_object_path == f"test-bucket/{resource_id}/data/contents/{folder_prefix}{file_name}"
    assert md.file_updated is True
    assert md.resource_contents_path == f"test-bucket/{resource_id}/data/contents"
    assert md.resource_md_path == f"test-bucket/{resource_id}/.hsmetadata"
    assert md.resource_md_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld"
    assert md.content_type == ContentType.RASTER
    assert md.system_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/system_metadata.json"
    assert md.user_metadata_path == f"test-bucket/{resource_id}/.hsmetadata/user_metadata.json"
    assert md.resource_metadata_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json"
    assert md.resource_associated_media_jsonld_path == f"test-bucket/{resource_id}/.hsjsonld/file_manifest.json"


@pytest.mark.parametrize("use_folder", [True, False])
def test_metadataobject_from_user_metadata_missing_content(use_folder):
    resource_id = str(uuid.uuid4())
    folder_prefix = "test-folder/" if use_folder else ""
    file_name = "logan1.tif"
    user_meta_file_name = f"{file_name}.user_metadata.json"
    md = determine_metadata_object_from_user_metadata(
        f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}{user_meta_file_name}", True
    )
    assert isinstance(md, BaseMetadataObject)
    assert not isinstance(md, RasterMetadataObject)
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


@pytest.mark.parametrize("use_folder", [True, False])
@pytest.mark.parametrize("use_vrt", [True, False])
def test_raster_is_content_type(use_folder, use_vrt):
    resource_id = str(uuid.uuid4())
    folder_prefix = "raster_aggregation/" if use_folder else ""
    base_file_name = "logan.vrt" if use_vrt else "logan1.tif"
    content_path = f"test-bucket/{resource_id}/data/contents/{folder_prefix}{base_file_name}"
    assert RasterMetadataObject.is_content_type(content_path) is True


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=1)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}logan1.tif.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert len(result_metadata["associatedMedia"]) == 1
    assert result_metadata["associatedMedia"][
        0]["name"] == "logan1.tif"
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][
        0]["url"].endswith("dataset_metadata.json")
    assert result_metadata[
        "user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/rasters/single/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")

    # Wait for metadata to be consistent
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan1.tif.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan1.tif.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_vrt(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(
            f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan2.tif")

    # Wait for metadata to be consistent
    sleep(2)
    # read in the resulting resource metadata file
    result_resource_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/dataset_metadata.json")

    assert_manifest_reference(result_resource_metadata, resource_id, "test-bucket", expected_media_obj_count=3)
    assert_has_part_reference(result_resource_metadata, resource_id, "test-bucket", expected_has_part_count=1)
    result_has_parts = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/has_parts.json")
    assert len(result_has_parts) == 1
    assert result_has_parts[0]["url"].endswith(f"{folder_prefix}logan.vrt.json")

    result_metadata = read_s3_json(
        f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert len(result_metadata["associatedMedia"]) == 3
    assert result_metadata["associatedMedia"][0]["name"] in ["logan.vrt", "logan1.tif", "logan2.tif"]
    assert len(result_metadata["isPartOf"]) == 1
    assert result_metadata["isPartOf"][0]["url"].endswith("dataset_metadata.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"


@pytest.mark.parametrize("use_folder", [True, False])
def test_raster_vrt_usermetadata(use_folder):
    resource_id = str(uuid.uuid4())  # Generate a random hex resource ID
    folder_prefix = "raster_aggregation/" if use_folder else ""
    print(resource_id)
    with open("tests/test_files/rasters/logan.vrt", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan.vrt")
    with open("tests/test_files/rasters/logan1.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan1.tif")
    with open("tests/test_files/rasters/logan2.tif", "rb") as f:
        s3_client.upload_fileobj(f, "test-bucket", f"{resource_id}/data/contents/{folder_prefix}logan2.tif")

    # Wait for metadata to be consistent
    sleep(2)
    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert "user_metadata" not in result_metadata

    write_s3_json(f"test-bucket/{resource_id}/.hsmetadata/{folder_prefix}logan.vrt.user_metadata.json", {
                  "user_metadata": "this is raster user metadata"})
    sleep(1)

    result_metadata = read_s3_json(f"test-bucket/{resource_id}/.hsjsonld/{folder_prefix}logan.vrt.json")
    assert result_metadata["user_metadata"] == "this is raster user metadata"
