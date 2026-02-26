import logging
import os
from typing import Optional
from urllib.parse import urlencode, quote

import boto3
import httpx
from botocore.client import Config
from fastapi import Response

logger = logging.getLogger("hs_auth_proxy")


class S3ProxyClient:
    """Proxies S3 requests to a backend S3-compatible storage service."""

    def __init__(self):
        self.backend_url = os.environ.get("S3_BACKEND_URL", "http://localhost:9000")
        self.backend_access_key = os.environ.get("S3_BACKEND_ACCESS_KEY", "")
        self.backend_secret_key = os.environ.get("S3_BACKEND_SECRET_KEY", "")
        self.timeout = float(os.environ.get("S3_PROXY_TIMEOUT", "300"))

        if self.backend_access_key and self.backend_secret_key:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.backend_url,
                aws_access_key_id=self.backend_access_key,
                aws_secret_access_key=self.backend_secret_key,
                config=Config(signature_version='s3v4'),
                region_name='auto'
            )
        else:
            self.s3_client = None

        logger.info(f"S3 Proxy initialized with backend: {self.backend_url}")

    async def proxy_request(
        self,
        method: str,
        path: str,
        headers: dict,
        query_params: dict,
        body: Optional[bytes] = None
    ) -> Response:
        """Proxy an S3 request to the backend storage."""
        path_parts = [p for p in path.split('/') if p]
        if len(path_parts) < 2:
            return Response(content=b"Invalid path", status_code=400,
                            headers={"Content-Type": "text/plain"})

        bucket = path_parts[0]
        key = '/'.join(path_parts[1:])

        logger.info(f"Proxying {method} request to bucket={bucket}, key={key}")

        if self.s3_client and method == "GET":
            try:
                response = self.s3_client.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read()

                response_headers = {}
                if 'ContentType' in response:
                    response_headers['Content-Type'] = response['ContentType']
                if 'ContentLength' in response:
                    response_headers['Content-Length'] = str(response['ContentLength'])
                if 'ETag' in response:
                    response_headers['ETag'] = response['ETag']
                if 'LastModified' in response:
                    response_headers['Last-Modified'] = response['LastModified'].strftime(
                        '%a, %d %b %Y %H:%M:%S GMT')

                return Response(content=content, status_code=200, headers=response_headers)

            except Exception as e:
                logger.error(f"Error getting object from S3: {e}")
                return Response(content=str(e).encode(), status_code=500,
                                headers={"Content-Type": "text/plain"})

        # Fall back to manual HTTP request for non-GET or when no boto3 client
        encoded_parts = [quote(part, safe='') for part in path.split('/')]
        encoded_path = '/'.join(encoded_parts)
        url = f"{self.backend_url}{encoded_path}"
        if query_params:
            url = f"{url}?{urlencode(query_params)}"

        filtered_headers = self._filter_headers(headers)
        logger.info(f"Proxying {method} request to {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method, url=url, headers=filtered_headers,
                    content=body, follow_redirects=False
                )
                response_headers = self._filter_response_headers(dict(response.headers))
                return Response(content=response.content, status_code=response.status_code,
                                headers=response_headers)

        except httpx.TimeoutException:
            logger.error("Timeout proxying request")
            return Response(content=b"Gateway Timeout", status_code=504,
                            headers={"Content-Type": "text/plain"})
        except httpx.RequestError as e:
            logger.error(f"Error proxying request: {e}")
            return Response(content=b"Bad Gateway", status_code=502,
                            headers={"Content-Type": "text/plain"})

    def _filter_headers(self, headers: dict) -> dict:
        """Filter out hop-by-hop and auth headers that shouldn't be forwarded."""
        exclude = {
            'host', 'connection', 'keep-alive', 'proxy-authenticate',
            'proxy-authorization', 'te', 'trailer', 'transfer-encoding',
            'upgrade', 'cookie', 'authorization'
        }
        return {k: v for k, v in headers.items() if k.lower() not in exclude}

    def _filter_response_headers(self, headers: dict) -> dict:
        """Filter out hop-by-hop headers from the backend response."""
        exclude = {
            'connection', 'keep-alive', 'proxy-authenticate', 'proxy-authorization',
            'te', 'trailer', 'transfer-encoding', 'upgrade',
            'content-encoding', 'content-length'
        }
        return {k: v for k, v in headers.items() if k.lower() not in exclude}
