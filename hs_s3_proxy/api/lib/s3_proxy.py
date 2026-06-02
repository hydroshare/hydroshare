import logging
import os
from typing import Optional
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

import httpx
from botocore.auth import S3SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.credentials import Credentials
from fastapi import Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

logger = logging.getLogger("hs_s3_proxy")
DEBUG_HEADERS = os.environ.get("S3_PROXY_DEBUG_HEADERS", "true").lower() == "true"


def _encode_query_params(query_params: dict) -> str:
    # Use RFC3986 encoding (space -> %20, not '+') for SigV4 compatibility.
    encoded_pairs = []
    for key, value in query_params.items():
        encoded_key = quote(str(key), safe='-_.~')
        encoded_value = quote(str(value), safe='-_.~')
        encoded_pairs.append((encoded_key, encoded_value))
    encoded_pairs.sort(key=lambda pair: (pair[0], pair[1]))
    return '&'.join(f"{k}={v}" for k, v in encoded_pairs)


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
        query_params = self._strip_presign_auth_query_params(query_params)

        encoded_parts = [quote(part, safe='') for part in path.split('/')]
        encoded_path = '/'.join(encoded_parts)
        url = f"{self.backend_url}{encoded_path}"
        if query_params:
            url = f"{url}?{_encode_query_params(query_params)}"

        outbound_headers = self._filter_headers(headers)
        # Force uncompressed backend responses so the proxy can stream raw bytes
        # without needing to decompress or re-advertise encoding to the client.
        outbound_headers['accept-encoding'] = 'identity'
        # Avoid compressed upstream payloads so stream length semantics remain stable.
        outbound_body = body or b""

        if self._signer:
            aws_req = AWSRequest(method=method, url=url, data=outbound_body, headers=outbound_headers)
            self._signer.add_auth(aws_req)
            outbound_headers = dict(aws_req.headers)

        logger.info(f"Proxying {method} request to {url}")

        try:
            client = httpx.AsyncClient(timeout=self.timeout)
            request = client.build_request(
                method=method,
                url=url,
                headers=outbound_headers,
                content=outbound_body if outbound_body else None,
            )
            response = await client.send(request, stream=True, follow_redirects=False)
            response_headers = self._filter_response_headers(dict(response.headers))
            # For streamed responses, avoid strict length assertions on downstream
            # when upstream content encoding/decoding behavior differs by transport.
            if method.upper() != "HEAD":
                response_headers.pop("content-length", None)
                response_headers.pop("Content-Length", None)
            if DEBUG_HEADERS:
                logger.info(
                    "Proxy response debug: status=%s backend_header_names=%s outgoing_header_names=%s",
                    response.status_code,
                    sorted(response.headers.keys()),
                    sorted(response_headers.keys()),
                )

            async def _close_stream() -> None:
                await response.aclose()
                await client.aclose()

            return StreamingResponse(
                # Preserve exact upstream bytes to keep Content-Length accurate.
                response.aiter_raw(),
                status_code=response.status_code,
                headers=response_headers,
                background=BackgroundTask(_close_stream),
            )

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
            })
        }

    def _filter_response_headers(self, headers: dict) -> dict:
        """Return only browser-safe response headers from the backend.

        For successful object fetches we do not want to leak arbitrary upstream
        headers back to the browser. Keep the S3/object metadata that matters to
        clients and drop everything else, especially anything cookie-related.
        """
        allow = {
            'accept-ranges',
            'cache-control',
            'content-disposition',
            'content-encoding',
            'content-length',
            'content-language',
            'content-range',
            'content-type',
            'etag',
            'expires',
            'last-modified',
            'x-amz-delete-marker',
            'x-amz-expiration',
            'x-amz-mp-parts-count',
            'x-amz-restore',
            'x-amz-server-side-encryption',
            'x-amz-version-id',
            'x-goog-generation',
            'x-goog-hash',
            'x-goog-metageneration',
            'x-goog-storage-class',
        }
        return {k: v for k, v in headers.items() if k.lower() in allow}

    def _strip_presign_auth_query_params(self, query_params: dict) -> dict:
        """Drop SigV4 presigned auth params before backend re-signing.

        The proxy authenticates/authorizes client requests itself, then signs
        upstream calls with backend credentials. Forwarding client presign
        signature fields would create mixed auth types at the backend.
        """
        if not query_params:
            return query_params

        sigv4_query_fields = {
            'x-amz-algorithm',
            'x-amz-credential',
            'x-amz-date',
            'x-amz-expires',
            'x-amz-signedheaders',
            'x-amz-signature',
            'x-amz-security-token',
            'x-amz-content-sha256',
        }
        return {
            k: v for k, v in query_params.items()
            if str(k).lower() not in sigv4_query_fields
        }
