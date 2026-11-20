"""HTTP-level tests for S3 download events, runnable without pytest."""

import asyncio
import unittest
from unittest.mock import patch

import httpx
from fastapi import Response
from fastapi.responses import StreamingResponse
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
        event_url = patch("api.lib.event_service.AUTH_SERVICE_URL", "http://auth.test")
        event = patch(
            "api.lib.event_service.DOWNLOAD_EVENT_CLIENT.post",
            return_value=httpx.Response(204),
        )
        for boundary in (signature, zone, event_url):
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
        self.event_post.assert_awaited_once_with(
            "http://auth.test/s3/event/",
            json={
                "action": "s3:GetObject",
                "bucket": "resource",
                "object_path": OBJECT_PATH,
                "username": "test-user",
                "user_id": 42,
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
        self.event_post.assert_awaited_once()
        self.assertEqual(self.event_post.await_args.kwargs["json"]["action"], "s3:GetObject")

    def test_tracking_waits_until_response_body_is_sent(self):
        body_sent = False
        response_state_at_post = []

        async def chunks():
            yield b"file"
            yield b" contents"

        async def observe_response(scope, receive, send):
            async def observe_send(message):
                nonlocal body_sent
                await send(message)
                if message["type"] == "http.response.body" and not message.get("more_body"):
                    body_sent = True

            await app(scope, receive, observe_send)

        async def post_event(*args, **kwargs):
            response_state_at_post.append(body_sent)
            return httpx.Response(204)

        self.backend.return_value = StreamingResponse(chunks())
        self.event_post.side_effect = post_event
        client = TestClient(observe_response, headers={"Authorization": AUTHORIZATION})
        self.addCleanup(client.close)
        response = client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.content, b"file contents")
        self.assertEqual(response_state_at_post, [True])

    def test_auth_failure_leaves_download_unchanged(self):
        self.event_post.return_value = httpx.Response(503)
        with self.assertLogs("hs_s3_proxy", level="WARNING") as logs:
            response = self.client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"file contents")
        self.event_post.assert_awaited_once()
        self.assertTrue(any("S3 download tracking returned HTTP 503" in entry for entry in logs.output))

    def test_slow_auth_notification_is_cancelled(self):
        async def slow_post(*args, **kwargs):
            await asyncio.sleep(10)

        self.event_post.side_effect = slow_post
        with self.assertLogs("hs_s3_proxy", level="WARNING") as logs:
            response = self.client.get(f"/resource/{OBJECT_PATH}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"file contents")
        self.event_post.assert_awaited_once()
        self.assertTrue(any("S3 download tracking timed out" in entry for entry in logs.output))

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

    def test_write_and_delete_keep_using_the_existing_notifier(self):
        self.backend.return_value = Response(status_code=204)
        with patch(
            "api.lib.event_service.EVENT_SERVICE_CLIENT.post",
            return_value=httpx.Response(204),
        ) as mutation_post:
            for method in ("PUT", "DELETE"):
                with self.subTest(method=method):
                    response = self.client.request(method, f"/resource/{OBJECT_PATH}")
                    self.assertEqual(response.status_code, 204)

        self.assertEqual(
            [call.kwargs["json"]["action"] for call in mutation_post.call_args_list],
            ["s3:PutObject", "s3:DeleteObject"],
        )
        self.event_post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
