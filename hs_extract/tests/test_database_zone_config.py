import requests
import pytest

from hsextract.utils import s3


def test_remote_zone_config_is_used_for_worker(monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("test-token", encoding="utf-8")
    monkeypatch.setenv("S3_ZONE_CONFIG_URL", "http://hydroshare/_internal/s3-zones/")
    monkeypatch.setenv("S3_ZONE_API_TOKEN_FILE", str(token_file))
    calls = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"hydroshare": {
                "bucket_name": "resource", "aws_s3_endpoint_url": "http://minio:9000",
                "aws_access_key_id": "key", "aws_secret_access_key": "secret", "region": "region-1",
            }}

    def get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return Response()

    monkeypatch.setattr(s3.requests, "get", get)
    result = s3._parse_zone_config()
    assert result["hydroshare"]["buckets"] == ["resource"]
    assert result["hydroshare"]["endpoint_url"] == "http://minio:9000"
    assert result["hydroshare"]["aws_secret_access_key"] == "secret"
    assert result["hydroshare"]["region"] == "region-1"
    assert calls[0][1] == {"Authorization": "Bearer test-token"}


def test_remote_zone_failure_does_not_use_environment_fallback(monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("test-token", encoding="utf-8")
    monkeypatch.setenv("S3_ZONE_CONFIG_URL", "http://hydroshare/_internal/s3-zones/")
    monkeypatch.setenv("S3_ZONE_API_TOKEN_FILE", str(token_file))
    monkeypatch.setenv("S3_ZONE_CONFIG", '{"unsafe": {}}')

    def fail(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr(s3.requests, "get", fail)
    with pytest.raises(requests.Timeout):
        s3._parse_zone_config()
