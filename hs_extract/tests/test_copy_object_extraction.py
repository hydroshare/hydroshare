from unittest.mock import MagicMock, patch

from hsextract.content_types.models import ContentType
from hsextract.main import refresh_or_extract_copied_file

KEY = "ciroh/res1/data/contents/file.nc"
SIDECAR = "ciroh/res1/.hsmetadata/file.nc.json"


def _md(content_type: ContentType) -> MagicMock:
    md = MagicMock()
    md.content_type = content_type
    md.content_type_md_path = SIDECAR
    md.zone = "ciroh"
    return md


def _run(md, sidecar_exists):
    with patch("hsextract.main.determine_metadata_object", return_value=md) as determine, \
            patch("hsextract.main.metadata_exists", return_value=sidecar_exists) as exists, \
            patch("hsextract.main.write_content_type_jsonld_metadata") as write_jsonld, \
            patch("hsextract.main.workflow_metadata_extraction") as workflow:
        refresh_or_extract_copied_file(KEY, 100, "ciroh")
    return determine, exists, write_jsonld, workflow


def test_copy_with_extracted_metadata_only_refreshes_jsonld():
    """A quota holder move copies the extracted metadata along with the file, so only the jsonld (with its
    bucket-qualified URLs) is regenerated and the file is not re-extracted."""
    md = _md(ContentType.NETCDF)
    determine, exists, write_jsonld, workflow = _run(md, sidecar_exists=True)
    determine.assert_called_once_with(KEY, True, "ciroh")
    exists.assert_called_once_with(SIDECAR, "ciroh")
    write_jsonld.assert_called_once_with(md)
    workflow.assert_not_called()
    md.extract_metadata.assert_not_called()


def test_copy_without_extracted_metadata_runs_full_extraction():
    """A resource copy copies only the data files, so the copy is extracted like a new upload."""
    md = _md(ContentType.NETCDF)
    _, _, write_jsonld, workflow = _run(md, sidecar_exists=False)
    workflow.assert_called_once_with(KEY, 100, True, "ciroh")
    write_jsonld.assert_not_called()


def test_copy_of_unknown_content_type_does_nothing():
    """A copy of a file with unknown content type does not trigger any extraction or jsonld refresh."""
    md = _md(ContentType.UNKNOWN)
    _, exists, write_jsonld, workflow = _run(md, sidecar_exists=True)
    exists.assert_not_called()
    write_jsonld.assert_not_called()
    workflow.assert_not_called()


def _run_task(action, **kwargs):
    from hs_extract.tasks import extract_metadata

    with patch("hs_extract.hsextract.main.refresh_or_extract_copied_file") as refresh_or_extract, \
            patch("hs_extract.hsextract.main.workflow_metadata_extraction") as workflow:
        extract_metadata.run(action=action, bucket="ciroh", object_path="res1/data/contents/file.nc",
                             file_size=100, zone="ciroh", **kwargs)
    return refresh_or_extract, workflow


def test_task_routes_copy_to_another_bucket_to_copy_handler():
    """A quota holder move copies each object to the same key in the new bucket."""
    refresh_or_extract, workflow = _run_task("s3:CopyObject", copy_source="resource/res1/data/contents/file.nc")
    refresh_or_extract.assert_called_once_with(KEY, 100, "ciroh")
    workflow.assert_not_called()


def test_task_routes_copy_to_another_resource_to_copy_handler():
    """A whole resource copied to a new resource id keeps each file's path within the resource."""
    refresh_or_extract, workflow = _run_task("s3:CopyObject", copy_source="ciroh/res0/data/contents/file.nc")
    refresh_or_extract.assert_called_once_with(KEY, 100, "ciroh")
    workflow.assert_not_called()


def test_task_routes_rename_copy_to_extraction():
    """A rename/move may land on an existing file whose sidecar is still in place, so it must be re-extracted."""
    refresh_or_extract, workflow = _run_task("s3:CopyObject", copy_source="ciroh/res1/data/contents/old.nc")
    workflow.assert_called_once_with(KEY, 100, True, "ciroh")
    refresh_or_extract.assert_not_called()


def test_task_routes_copy_without_source_to_extraction():
    """A copy event without a source (e.g. queued before copy_source was added) triggers extraction."""
    refresh_or_extract, workflow = _run_task("s3:CopyObject")
    workflow.assert_called_once_with(KEY, 100, True, "ciroh")
    refresh_or_extract.assert_not_called()


def test_task_routes_put_object_to_extraction():
    """A direct put object triggers extraction."""
    refresh_or_extract, workflow = _run_task("s3:PutObject")
    workflow.assert_called_once_with(KEY, 100, True, "ciroh")
    refresh_or_extract.assert_not_called()
