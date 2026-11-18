import pytest
from fastapi import FastAPI, Response
from httpx import ASGITransport, AsyncClient

from api.routes import external


OWNED = "a" * 32
PRIVATE = "b" * 32
AUTHORIZATION = (
    "AWS4-HMAC-SHA256 Credential=test/20260101/auto/s3/aws4_request, "
    "SignedHeaders=host, Signature=test"
)


@pytest.mark.asyncio
async def test_object_request_cannot_authorize_with_another_resource_prefix(monkeypatch):
    app = FastAPI()
    app.include_router(external.router)
    forwarded = []

    monkeypatch.setattr(external, "_verify_sigv4_request", lambda **kwargs: (1, None))
    monkeypatch.setattr(
        external, "check_s3_authorization",
        lambda **kwargs: kwargs["object_path"].startswith(f"{OWNED}/"),
    )

    async def proxy_request(**kwargs):
        forwarded.append(kwargs["path"])
        return Response(content=b"private data")

    monkeypatch.setattr(external.s3_proxy, "proxy_request", proxy_request)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/resource/{PRIVATE}/data/contents/private.txt",
            params={"prefix": f"{OWNED}/data/contents/"},
            headers={"Authorization": AUTHORIZATION},
        )

    assert response.status_code == 403
    assert forwarded == []
