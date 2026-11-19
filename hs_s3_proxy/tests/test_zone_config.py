import httpx
import pytest

from hs_s3_proxy.api.lib import zone_config
from hs_s3_proxy.api.lib.s3_proxy import _load_zone_config


@pytest.fixture
def remote_zone(monkeypatch, tmp_path):
    token_file = tmp_path / "token"
    token_file.write_text("test-token", encoding="utf-8")
    monkeypatch.setenv("S3_ZONE_CONFIG_URL", "http://hydroshare/_internal/s3-zones/")
    monkeypatch.setenv("S3_ZONE_API_TOKEN_FILE", str(token_file))
    zone_config._remote_config.cache_clear()
    yield
    zone_config._remote_config.cache_clear()


def test_remote_zone_configuration_builds_signer(monkeypatch, remote_zone):
    calls = []

    def get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return httpx.Response(200, request=httpx.Request("GET", url), json={
            "hydroshare": {
                "bucket_name": "resource", "alias": "res", "aws_s3_endpoint_url": "http://minio:9000",
                "aws_access_key_id": "local-key", "aws_secret_access_key": "local-secret",
            }
        })

    monkeypatch.setattr(zone_config.httpx, "get", get)
    backends = _load_zone_config()
    assert backends["res"] is backends["resource"]
    assert backends["resource"].signer.credentials.access_key == "local-key"
    assert calls[0][1] == {"Authorization": "Bearer test-token"}
    _load_zone_config()
    assert len(calls) == 1


def test_remote_zone_failure_does_not_use_environment_fallback(monkeypatch, remote_zone):
    monkeypatch.setenv("S3_ZONE_CONFIG", '{"unsafe": {}}')
    monkeypatch.setattr(
        zone_config.httpx, "get",
        lambda url, **kwargs: httpx.Response(403, request=httpx.Request("GET", url)),
    )
    with pytest.raises(httpx.HTTPStatusError):
        _load_zone_config()
