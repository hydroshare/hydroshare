from hsextract.utils import file as file_utils


def test_file_metadata_uses_s3_head_metadata(monkeypatch):
    def fake_get_object_size_and_checksum(bucket, key, zone):
        assert bucket == "resource"
        assert key == "abc/data/contents/report.csv"
        assert zone == "hydroshare"
        return 2048, "deadbeef"

    monkeypatch.setattr(file_utils, "_get_object_size_and_checksum", fake_get_object_size_and_checksum)

    metadata = file_utils.file_metadata("resource/abc/data/contents/report.csv", "hydroshare")

    assert metadata.name == "report.csv"
    assert metadata.sha256 == "deadbeef"
    assert metadata.contentSize == "2.048 KB"
    assert metadata.encodingFormat == "text/csv"


def test_file_metadata_preserves_directory_fallback():
    metadata = file_utils.file_metadata("resource/abc/data/contents/folder/", "hydroshare")

    assert metadata.name == ""
    assert metadata.sha256 == "N/A"
    assert metadata.contentSize == "0 KB"
    assert metadata.encodingFormat == ""
