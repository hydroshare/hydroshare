from datetime import datetime
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import boto3
from botocore.config import Config
from django.test import SimpleTestCase

from django_s3.settings import ZoneConfig
from django_s3.storage import S3Storage


class PublicDownloadURLTests(SimpleTestCase):
    def setUp(self):
        self.zone = ZoneConfig(
            bucket_name="resource",
            aws_s3_endpoint_url="http://minio:9000",
            aws_s3_endpoint_url_public="http://localhost:9000",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
        )

    def test_signed_download_uses_public_endpoint(self):
        with patch("django_s3.s3_backend.bucket_and_zone", return_value=("resource", "hydroshare")), \
             patch("django_s3.s3_backend.get_zone_config", return_value=self.zone), \
             patch("botocore.auth.datetime.datetime", wraps=datetime) as clock:
            clock.utcnow.return_value = datetime(2026, 1, 1, 0, 0, 0)
            storage = S3Storage()
            storage.querystring_expire = 3600
            url = storage.signed_url(
                "resource-id/data/contents/file.txt",
                ResponseContentDisposition='attachment; filename="file.txt"',
            )
            client = boto3.client(
                "s3", endpoint_url=self.zone.aws_s3_endpoint_url_public,
                aws_access_key_id=self.zone.aws_access_key_id, aws_secret_access_key=self.zone.aws_secret_access_key,
                region_name="auto", config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            )
            expected = client.generate_presigned_url(
                "get_object", Params={
                    "Bucket": "resource", "Key": "resource-id/data/contents/file.txt",
                    "ResponseContentDisposition": 'attachment; filename="file.txt"',
                }, ExpiresIn=3600, HttpMethod=None,
            )
        actual_parts, expected_parts = urlsplit(url), urlsplit(expected)
        self.assertEqual(actual_parts.netloc, "localhost:9000")
        self.assertEqual(actual_parts.path, "/resource/resource-id/data/contents/file.txt")
        self.assertEqual(parse_qs(actual_parts.query), parse_qs(expected_parts.query))

    def test_unsigned_download_uses_public_endpoint(self):
        with patch("django_s3.s3_backend.bucket_and_zone", return_value=("resource", "hydroshare")), \
             patch("django_s3.s3_backend.get_zone_config", return_value=self.zone):
            storage = S3Storage()
            storage.querystring_auth = False
            url = storage.signed_url("resource-id/data/contents/file.txt")
        parts = urlsplit(url)
        self.assertEqual(parts.netloc, "localhost:9000")
        self.assertEqual(parts.path, "/resource/resource-id/data/contents/file.txt")
        self.assertNotIn("X-Amz-Signature", parse_qs(parts.query))
