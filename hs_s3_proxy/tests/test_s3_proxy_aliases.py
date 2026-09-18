import json

import httpx
import pytest

from hs_s3_proxy.api.lib.s3_proxy import S3ProxyClient


def test_bucket_aliases_are_accepted(monkeypatch):
    monkeypatch.setenv(
        "S3_ZONE_CONFIG",
        json.dumps(
            {
                "hydroshare": {
                    "bucket_name": "resource",
                    "endpoint": "http://minio:9000",
                    "access_key": "cuahsi",
                    "secret_key": "devpassword",
                    "zone": "hydroshare",
                    "alias": "hydroshare-resource",
                }
            }
        ),
    )

    proxy = S3ProxyClient()

    assert proxy.is_configured_bucket("resource")
    assert proxy.is_configured_bucket("hydroshare-resource")
    assert not proxy.is_configured_bucket("hydroshare")
    assert proxy.zone_for_bucket("hydroshare-resource") == "hydroshare"
    assert proxy._backend_for_bucket("resource") is proxy._backend_for_bucket("hydroshare-resource")


@pytest.mark.asyncio
async def test_proxy_request_rewrites_alias_to_bucket_name(monkeypatch):
    monkeypatch.setenv(
        "S3_ZONE_CONFIG",
        json.dumps(
            {
                "hydroshare": {
                    "bucket_name": "resource",
                    "endpoint": "http://minio:9000",
                    "access_key": "cuahsi",
                    "secret_key": "devpassword",
                    "zone": "hydroshare",
                    "alias": "hydroshare-resource",
                }
            }
        ),
    )

    proxy = S3ProxyClient()

    captured = {}

    async def fake_request(method, url, headers=None, content=None, follow_redirects=None):
        captured["url"] = url
        return httpx.Response(200, request=httpx.Request(method, url))

    monkeypatch.setattr(proxy._client, "request", fake_request)

    await proxy.proxy_request(
        method="GET", path="/hydroshare-resource/some/object.txt",
        headers={}, query_params={},
    )

    assert captured["url"] == "http://minio:9000/resource/some/object.txt"
