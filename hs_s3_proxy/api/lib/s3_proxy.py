import logging
import os
import json
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
        self.region = os.environ.get("S3_BACKEND_REGION", "auto")
        self.timeout = float(os.environ.get("S3_PROXY_TIMEOUT", "300"))
        self._zone_backends = self._load_zone_backends()
        self._default_zone_name = (
            os.environ.get("S3_BACKEND_DEFAULT_ZONE")
            or os.environ.get("RESOURCE_S3_DEFAULT_ZONE")
            or ""
        )
        self._default_zone_bucket = self._resolve_default_zone_bucket()

        if not self._zone_backends:
            raise ValueError(
                "No backend zones configured. Set S3_BACKEND_ZONES_CONFIG or RESOURCE_S3_ZONES_CONFIG."
            )

        configured_buckets = sorted(self._zone_backends.keys())
        logger.info(
            "S3 Proxy initialized with multi-zone backend config for buckets=%s default_zone=%s",
            configured_buckets,
            self._default_zone_name or "<unset>",
        )

    def _make_backend_target(self, endpoint_url: str, access_key: str, secret_key: str, region: str) -> dict:
        signer = None
        if access_key and secret_key:
            signer = S3SigV4Auth(Credentials(access_key, secret_key), "s3", region)
        return {
            "endpoint_url": endpoint_url,
            "access_key": access_key,
            "secret_key": secret_key,
            "region": region,
            "signer": signer,
        }

    def _load_zone_backends(self) -> dict[str, dict]:
        raw = os.environ.get("S3_BACKEND_ZONES_CONFIG") or os.environ.get("RESOURCE_S3_ZONES_CONFIG")
        if not raw:
            return {}

        try:
            zones_config = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("Invalid zones config JSON: %s", e)
            return {}

        if not isinstance(zones_config, dict):
            logger.error("Zones config must be a JSON object")
            return {}

        bucket_backends = {}
        for zone_name, cfg in zones_config.items():
            if not isinstance(cfg, dict):
                logger.warning("Skipping zone %s: config must be an object", zone_name)
                continue

            bucket_name = cfg.get("bucket_name")
            endpoint_url = cfg.get("aws_s3_endpoint_url") or cfg.get("backend_url")
            access_key = cfg.get("aws_access_key_id", "")
            secret_key = cfg.get("aws_secret_access_key", "")
            region = cfg.get("aws_region") or self.region

            if not bucket_name or not endpoint_url:
                logger.warning(
                    "Skipping zone %s: both bucket_name and aws_s3_endpoint_url are required",
                    zone_name,
                )
                continue

            bucket_backends[bucket_name] = self._make_backend_target(
                endpoint_url=endpoint_url,
                access_key=access_key,
                secret_key=secret_key,
                region=region,
            )

        return bucket_backends

    def _resolve_default_zone_bucket(self) -> Optional[str]:
        if not self._default_zone_name:
            return None

        raw = os.environ.get("S3_BACKEND_ZONES_CONFIG") or os.environ.get("RESOURCE_S3_ZONES_CONFIG")
        if not raw:
            return None

        try:
            zones_config = json.loads(raw)
        except json.JSONDecodeError:
            return None

        cfg = zones_config.get(self._default_zone_name, {}) if isinstance(zones_config, dict) else {}
        if isinstance(cfg, dict):
            return cfg.get("bucket_name")
        return None

    def _resolve_backend_target(self, path: str) -> dict:
        path_parts = [p for p in path.lstrip("/").split("/") if p]
        bucket_name = path_parts[0] if path_parts else None
        if bucket_name and bucket_name in self._zone_backends:
            return self._zone_backends[bucket_name]

        if self._default_zone_bucket and self._default_zone_bucket in self._zone_backends:
            return self._zone_backends[self._default_zone_bucket]

        # In multi-zone mode without a declared default zone, pick any configured
        # backend instead of falling back to legacy localhost defaults.
        return next(iter(self._zone_backends.values()))

    async def proxy_request(
        self,
        method: str,
        path: str,
        headers: dict,
        query_params: dict,
        body: Optional[bytes] = None
    ) -> Response:
        """Proxy an S3 request to the backend storage, re-signing with backend credentials."""
        backend = self._resolve_backend_target(path)
        encoded_parts = [quote(part, safe='') for part in path.split('/')]
        encoded_path = '/'.join(encoded_parts)
        url = f"{backend['endpoint_url']}{encoded_path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        outbound_headers = self._filter_headers(headers)
        outbound_body = body or b""

        if backend["signer"]:
            aws_req = AWSRequest(method=method, url=url, data=outbound_body, headers=outbound_headers)
            backend["signer"].add_auth(aws_req)
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
            })
        }

    def _filter_response_headers(self, headers: dict) -> dict:
        """Filter out hop-by-hop headers from the backend response."""
        exclude = {
            'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
            'te', 'trailer', 'transfer-encoding', 'upgrade',
            'content-encoding', 'content-length'
        }
        return {k: v for k, v in headers.items() if k.lower() not in exclude}
