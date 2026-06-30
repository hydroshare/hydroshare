import json
import logging
import os
from dataclasses import dataclass
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


@dataclass
class _ZoneBackend:
    """Per-bucket backend configuration resolved from S3_ZONE_CONFIG."""
    zone: str
    endpoint: str
    signer: Optional[S3SigV4Auth]


def _build_signer(access_key: str, secret_key: str, region: str) -> Optional[S3SigV4Auth]:
    if access_key and secret_key:
        return S3SigV4Auth(Credentials(access_key, secret_key), "s3", region)
    return None


def _load_zone_config() -> dict[str, _ZoneBackend]:
    """Parse S3_ZONE_CONFIG (JSON) into a bucket-name → _ZoneBackend map.

    Expected JSON shape::

        {
          "resource": {
            "zone":       "hydroshare",   // logical zone name (defaults to bucket name)
            "endpoint":   "http://minio:9000",
            "access_key": "cuahsi",
            "secret_key": "devpassword",
            "region":     "auto"          // optional, defaults to "auto"
          },
          "ciroh": { ... }
        }

    Buckets not present in the map are rejected with NoSuchBucket.
    """
    raw = os.environ.get("S3_ZONE_CONFIG", "").strip()
    if not raw:
        return {}

    try:
        mapping: dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(f"Invalid S3_ZONE_CONFIG JSON: {exc}")
        return {}

    backends: dict[str, _ZoneBackend] = {}
    for bucket, cfg in mapping.items():
        if not isinstance(cfg, dict):
            logger.warning(f"S3_ZONE_CONFIG: ignoring non-dict entry for bucket {bucket!r}")
            continue
        endpoint = cfg.get("endpoint")
        ak = cfg.get("access_key", "")
        sk = cfg.get("secret_key", "")
        region = cfg.get("region", "auto")
        zone_name = cfg.get("zone", bucket)
        if not endpoint:
            logger.warning(f"S3_ZONE_CONFIG: bucket {bucket!r} has no endpoint, skipping")
            continue
        backends[bucket] = _ZoneBackend(
            zone=zone_name,
            endpoint=endpoint,
            signer=_build_signer(ak, sk, region),
        )
        logger.info(f"Zone config: bucket={bucket!r} → zone={zone_name!r} endpoint={endpoint}")

    return backends


class S3ProxyClient:
    """Proxies S3 requests to a backend S3-compatible storage service.

    All bucket → backend routing is driven exclusively by S3_ZONE_CONFIG.
    Requests for unconfigured buckets are rejected with 404 NoSuchBucket.
    """

    def __init__(self):
        self.timeout = float(os.environ.get("S3_PROXY_TIMEOUT", "300"))
        self._zone_backends: dict[str, _ZoneBackend] = _load_zone_config()
        logger.info(f"S3 Proxy initialized: zone_buckets={sorted(self._zone_backends)}")

    # ------------------------------------------------------------------
    # Public helpers used by external.py for event routing
    # ------------------------------------------------------------------

    def zone_for_bucket(self, bucket: str) -> str:
        """Return the logical zone name for *bucket*, or the bucket name itself
        when no zone mapping is configured."""
        backend = self._zone_backends.get(bucket)
        return backend.zone if backend else bucket

    # ------------------------------------------------------------------
    # Internal routing
    # ------------------------------------------------------------------

    def _backend_for_bucket(self, bucket: str) -> Optional[_ZoneBackend]:
        """Return the _ZoneBackend for *bucket*, or None if not configured."""
        return self._zone_backends.get(bucket)

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

        # Resolve the bucket-specific backend; reject buckets not in zone config.
        bucket = path_parts[0]
        zone_backend = self._backend_for_bucket(bucket)
        if zone_backend is None:
            logger.warning(f"No zone config for bucket={bucket!r}")
            return Response(
                content=_s3_error_xml("NoSuchBucket", f"Bucket {bucket!r} is not served by this endpoint"),
                status_code=404, media_type="application/xml",
            )

        encoded_parts = [quote(part, safe='') for part in path.split('/')]
        encoded_path = '/'.join(encoded_parts)
        url = f"{zone_backend.endpoint}{encoded_path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        outbound_headers = self._filter_headers(headers)
        outbound_body = body or b""

        if zone_backend.signer:
            aws_req = AWSRequest(method=method, url=url, data=outbound_body, headers=outbound_headers)
            zone_backend.signer.add_auth(aws_req)
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
                and k.lower() not in {'x-amz-date', 'x-amz-content-sha256', 'x-amz-security-token', })
        }

    def _filter_response_headers(self, headers: dict) -> dict:
        """Filter out hop-by-hop headers from the backend response."""
        exclude = {
            'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
            'te', 'trailer', 'transfer-encoding', 'upgrade',
            'content-encoding', 'content-length'
        }
        return {k: v for k, v in headers.items() if k.lower() not in exclude}
