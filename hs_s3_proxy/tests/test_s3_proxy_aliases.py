import gzip
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
                    "aws_s3_endpoint_url": "http://minio:9000",
                    "aws_access_key_id": "cuahsi",
                    "aws_secret_access_key": "devpassword",
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
                    "aws_s3_endpoint_url": "http://minio:9000",
                    "aws_access_key_id": "cuahsi",
                    "aws_secret_access_key": "devpassword",
                    "alias": "hydroshare-resource",
                }
            }
        ),
    )

    proxy = S3ProxyClient()

    captured = {}

    async def fake_send(request, follow_redirects=None, stream=False):
        captured["url"] = str(request.url)
        captured["headers"] = request.headers
        return httpx.Response(200, request=request)

    monkeypatch.setattr(proxy._client, "send", fake_send)

    await proxy.proxy_request(
        method="GET", path="/hydroshare-resource/some/object.txt",
        headers={}, query_params={},
    )

    assert captured["url"] == "http://minio:9000/resource/some/object.txt"


@pytest.mark.asyncio
async def test_range_response_streams_raw_bytes(monkeypatch):
    monkeypatch.setenv(
        "S3_ZONE_CONFIG",
        json.dumps({
            "hydroshare": {
                "bucket_name": "resource",
                "aws_s3_endpoint_url": "http://minio:9000",
            }
        }),
    )
    proxy = S3ProxyClient()
    body = gzip.compress(b"range bytes")
    request_headers = {}

    async def fake_send(request, follow_redirects=None, stream=False):
        request_headers.update(request.headers)
        return httpx.Response(
            206,
            headers={
                "Content-Range": f"bytes 0-{len(body) - 1}/{len(body) * 2}",
                "Content-Length": str(len(body)),
                "Content-Encoding": "gzip",
            },
            stream=httpx.ByteStream(body),
            request=request,
        )

    monkeypatch.setattr(proxy._client, "send", fake_send)
    response = await proxy.proxy_request(
        method="GET",
        path="/resource/object.bin",
        headers={"range": f"bytes=0-{len(body) - 1}"},
        query_params={},
    )

    streamed_body = b"".join([chunk async for chunk in response.body_iterator])
    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 0-{len(body) - 1}/{len(body) * 2}"
    assert "content-length" not in response.headers
    assert request_headers["accept-encoding"] == "identity"
    assert streamed_body == body
