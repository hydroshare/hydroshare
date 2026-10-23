from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from hsextract.content_types.models import BaseMetadataObject
from hsextract.main import write_resource_jsonld_metadata
from hsextract.utils.s3 import metadata_exists


def _make_md() -> BaseMetadataObject:
    return BaseMetadataObject("resource/res1/data/contents/file.csv", False, "hydroshare")


def _fake_load(metadata_by_path: dict):
    return lambda path, zone: metadata_by_path.get(path, {})


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code}}, "HeadObject")


def test_skips_write_when_system_metadata_missing():
    """A bucket without system_metadata.json no longer holds the resource (e.g. after a quota holder move),
    so no dataset_metadata.json should be written there (#6497)."""
    md = _make_md()
    with patch("hsextract.main.load_metadata", side_effect=_fake_load({})), \
            patch("hsextract.main.metadata_exists", return_value=False), \
            patch("hsextract.main.write_metadata") as write_metadata:
        write_resource_jsonld_metadata(md)
    write_metadata.assert_not_called()


def test_skips_write_when_only_user_metadata_present():
    md = _make_md()
    metadata = {md.user_metadata_path: {"name": "user title"}}
    with patch("hsextract.main.load_metadata", side_effect=_fake_load(metadata)), \
            patch("hsextract.main.metadata_exists", return_value=False), \
            patch("hsextract.main.write_metadata") as write_metadata:
        write_resource_jsonld_metadata(md)
    write_metadata.assert_not_called()


def test_transient_head_error_raises_without_writing():
    """A transient S3 error must propagate so the task retries, rather than being treated as not found."""
    md = _make_md()
    client = MagicMock()
    client.head_object.side_effect = _client_error("503")
    with patch("hsextract.main.load_metadata", side_effect=_fake_load({})), \
            patch("hsextract.utils.s3._get_s3_client", return_value=client), \
            patch("hsextract.main.write_metadata") as write_metadata:
        with pytest.raises(ClientError):
            write_resource_jsonld_metadata(md)
    write_metadata.assert_not_called()


def test_not_found_head_skips_write():
    md = _make_md()
    client = MagicMock()
    client.head_object.side_effect = _client_error("404")
    with patch("hsextract.main.load_metadata", side_effect=_fake_load({})), \
            patch("hsextract.utils.s3._get_s3_client", return_value=client), \
            patch("hsextract.main.write_metadata") as write_metadata:
        write_resource_jsonld_metadata(md)
    client.head_object.assert_called_once_with(Bucket="resource", Key="res1/.hsmetadata/system_metadata.json")
    write_metadata.assert_not_called()


def test_existing_but_unloadable_system_metadata_raises_without_writing():
    """The file exists but could not be read (e.g. a failed GET), so retry instead of skipping."""
    md = _make_md()
    with patch("hsextract.main.load_metadata", side_effect=_fake_load({})), \
            patch("hsextract.main.metadata_exists", return_value=True), \
            patch("hsextract.main.write_metadata") as write_metadata:
        with pytest.raises(RuntimeError):
            write_resource_jsonld_metadata(md)
    write_metadata.assert_not_called()


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
def test_metadata_exists_false_on_not_found(code):
    client = MagicMock()
    client.head_object.side_effect = _client_error(code)
    with patch("hsextract.utils.s3._get_s3_client", return_value=client):
        assert metadata_exists("resource/res1/.hsmetadata/system_metadata.json", "hydroshare") is False


def test_metadata_exists_true_when_present():
    client = MagicMock()
    with patch("hsextract.utils.s3._get_s3_client", return_value=client):
        assert metadata_exists("resource/res1/.hsmetadata/system_metadata.json", "hydroshare") is True


def test_writes_when_system_metadata_present():
    md = _make_md()
    metadata = {
        md.system_metadata_path: {"resource_id": "res1", "doi": None},
        md.user_metadata_path: {"name": "user title"},
    }
    with patch("hsextract.main.load_metadata", side_effect=_fake_load(metadata)), \
            patch("hsextract.main.metadata_exists") as exists, \
            patch("hsextract.main.write_metadata") as write_metadata:
        write_resource_jsonld_metadata(md)
    exists.assert_not_called()
    write_metadata.assert_called_once_with(
        md.resource_metadata_jsonld_path,
        {"name": "user title", "resource_id": "res1", "doi": None},
        "hydroshare",
    )
