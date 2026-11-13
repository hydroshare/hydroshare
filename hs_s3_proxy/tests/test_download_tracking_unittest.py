"""HTTP-level tests for S3 download events, runnable without pytest."""

import unittest
from unittest.mock import patch

import httpx
from fastapi import Response
from fastapi.testclient import TestClient

from api.main import app


RESOURCE_ID = "0123456789abcdef0123456789abcdef"
OBJECT_PATH = f"{RESOURCE_ID}/data/contents/example.txt"
AUTHORIZATION = (
    "AWS4-HMAC-SHA256 Credential=test-user:test-key/20260101/auto/s3/aws4_request, "
    "SignedHeaders=host, Signature=test-signature"
)


class DownloadTrackingTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, headers={"Authorization": AUTHORIZATION})
        self.addCleanup(self.client.close)

        signature = patch(
            "api.routes.external.verify_signature_sync",
            return_value={"allow": True, "user_id": 42},
        )
        authorization = patch("api.routes.external.check_s3_authorization", return_value=True)
        backend = patch(
            "api.routes.external.s3_proxy.proxy_request",
            return_value=Response(content=b"file contents", status_code=200),
        )
        zone = patch("api.routes.external.s3_proxy.zone_for_bucket", return_value="hydroshare")
        event = patch(
            "api.lib.event_service.EVENT_SERVICE_CLIENT.post",
            return_value=httpx.Response(200),
        )
        for boundary in (signature, zone):
            boundary.start()
            self.addCleanup(boundary.stop)
        self.authorization = authorization.start()
        self.addCleanup(authorization.stop)
        self.backend = backend.start()
        self.addCleanup(backend.stop)
        self.event_post = event.start()
        self.addCleanup(event.stop)

    def test_successful_content_download_sends_event(self):
        response = self.client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"file contents")
        self.event_post.assert_called_once()
        self.assertEqual(
            self.event_post.call_args.kwargs["json"],
            {
                "action": "s3:GetObject",
                "bucket": "resource",
                "object_path": OBJECT_PATH,
                "username": "test-user",
                "user_id": 42,
                "file_size": 0,
                "zone": "hydroshare",
            },
        )

    def test_partial_content_download_sends_event(self):
        self.backend.return_value = Response(content=b"file", status_code=206)

        response = self.client.get(
            f"/resource/{OBJECT_PATH}", headers={"Range": "bytes=0-3"}
        )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"file")
        self.event_post.assert_called_once()
        self.assertEqual(self.event_post.call_args.kwargs["json"]["action"], "s3:GetObject")

    def test_failed_download_does_not_send_event(self):
        self.backend.return_value = Response(status_code=404)

        response = self.client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.status_code, 404)
        self.event_post.assert_not_called()

    def test_other_reads_do_not_send_download_events(self):
        cases = (
            ("GET", "/resource/not-a-resource/data/contents/example.txt"),
            ("GET", f"/resource/{RESOURCE_ID}/data/metadata.xml"),
            ("GET", f"/resource/{RESOURCE_ID}/data/contents/"),
            ("HEAD", f"/resource/{OBJECT_PATH}"),
            ("GET", "/resource?list-type=2"),
            ("GET", f"/resource/{OBJECT_PATH}?tagging"),
        )
        for method, path in cases:
            with self.subTest(method=method, path=path):
                response = self.client.request(method, path)
                self.assertEqual(response.status_code, 200)
                self.event_post.assert_not_called()

    def test_unauthorized_download_does_not_send_event(self):
        self.authorization.return_value = False

        response = self.client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.status_code, 403)
        self.backend.assert_not_called()
        self.event_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
