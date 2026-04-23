import logging
import os
from typing import Optional
from urllib.parse import urlencode, quote
from xml.sax.saxutils import escape as xml_escape

import httpx
from botocore.auth import S3SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from fastapi import Response

logger = logging.getLogger("hs_s3_proxy")


def _s3_error_xml(code: str, message: str) -> bytes:
    return (
        f"<?xml version='1.0' encoding='UTF-8'?>"
        f"<Error><Code>{xml_escape(code)}</Code>"
        f"<Message>{xml_escape(message)}</Message></Error>"
    ).encode("utf-8")


class S3ProxyClient:
    """Proxies S3 requests to a backend S3-compatible storage service."""

    def __init__(self):
        self.backend_url = os.environ.get("S3_BACKEND_URL", "http://localhost:9000")
        self.backend_access_key = os.environ.get("S3_BACKEND_ACCESS_KEY", "")
        self.backend_secret_key = os.environ.get("S3_BACKEND_SECRET_KEY", "")
        self.region = os.environ.get("S3_BACKEND_REGION", "auto")
        self.timeout = float(os.environ.get("S3_PROXY_TIMEOUT", "300"))

        if self.backend_access_key and self.backend_secret_key:
            self._signer = S3SigV4Auth(
                Credentials(self.backend_access_key, self.backend_secret_key),
                "s3", self.region,
            )
        else:
            self._signer = None

        logger.info(f"S3 Proxy initialized with backend: {self.backend_url}")

    async def proxy_request(
        self,
        method: str,
        path: str,
        headers: dict,
        query_params: dict,
        body: Optional[bytes] = None
    ) -> Response:
        """Proxy an S3 request to the backend storage, re-signing with backend credentials."""
        path_parts = [p for p in path.split('/') if p]
        if len(path_parts) < 2:
            return Response(
                content=_s3_error_xml("InvalidRequest", "Path must include a bucket and key"),
                status_code=400, media_type="application/xml",
            )

        encoded_parts = [quote(part, safe='') for part in path.split('/')]
        encoded_path = '/'.join(encoded_parts)
        url = f"{self.backend_url}{encoded_path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        outbound_headers = self._filter_headers(headers)
        outbound_body = body or b""

        if self._signer:
            aws_req = AWSRequest(method=method, url=url, data=outbound_body, headers=outbound_headers)
            self._signer.add_auth(aws_req)
            outbound_headers = dict(aws_req.headers)

        logger.info(f"Proxying {method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method, url=url, headers=outbound_headers,
                    content=outbound_body if outbound_body else None, follow_redirects=False,
                )
                response_headers = self._filter_response_headers(dict(response.headers))
                return Response(content=response.content, status_code=response.status_code,
                                headers=response_headers)

        except httpx.TimeoutException:
            logger.error("Timeout proxying request")
            return Response(
                content=_s3_error_xml("SlowDown", "Backend storage timed out"),
                status_code=504, media_type="application/xml",
            )
        except httpx.RequestError as e:
            logger.error(f"Error proxying request: {e}")
            return Response(
                content=_s3_error_xml("InternalError", "Backend storage unreachable"),
                status_code=502, media_type="application/xml",
            )

    def _filter_headers(self, headers: dict) -> dict:
        """Whitelist only the S3-meaningful request headers we want to forward.

        Anything we forward gets folded into the SigV4 canonical request by the signer.
        If a header is present at sign time but gets mutated in flight (by Cloud Run
        egress, the GCP frontend, or any hop in between), GCS will see a different
        canonical request and the signature will not match. We sidestep that by only
        forwarding headers S3 actually acts on, and letting httpx/the signer handle
        transport/auth headers itself.
        """
        allow = {
            # Request payload metadata
            'content-type', 'content-md5', 'content-encoding',
            'content-language', 'content-disposition',
            # Caching / conditional requests
            'cache-control', 'expires',
            'if-modified-since', 'if-unmodified-since',
            'if-match', 'if-none-match',
            'range',
        }
        return {
            k: v for k, v in headers.items()
            if k.lower() in allow
            or (k.lower().startswith('x-amz-')
                and k.lower() not in {
                    'x-amz-date', 'x-amz-content-sha256', 'x-amz-security-token',
                }
            )
        }

    def _filter_response_headers(self, headers: dict) -> dict:
        """Filter out hop-by-hop headers from the backend response."""
        exclude = {
            'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
            'te', 'trailer', 'transfer-encoding', 'upgrade',
            'content-encoding', 'content-length'
        }
        return {k: v for k, v in headers.items() if k.lower() not in exclude}
