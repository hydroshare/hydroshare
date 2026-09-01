"""
Integration tests for hs_s3_proxy covering:

  * list_objects_v2
  * get_object
  * put_object
  * delete_object
  * multipart upload (create → upload_part × N → complete)

Each operation is tested twice:
  - SigV4 service-account auth  (s3_client fixture / Test* classes)
  - Django session-cookie auth   (session_s3_client fixture / TestSession* classes)

Event-service checks (TestEventService) verify Celery tasks are enqueued in
Redis after write operations.

Run with the proxy and its dependencies live:
    pytest hs_s3_proxy/tests/test_s3_operations.py -v
"""
import io
import os
import threading
import time

import redis


# ---------------------------------------------------------------------------
# List objects
# ---------------------------------------------------------------------------

class TestListObjects:
    def test_list_objects_returns_ok(self, s3_client, test_bucket, test_resource_id):
        """list_objects_v2 on the test bucket/prefix should not raise."""
        kwargs = {"Bucket": test_bucket}
        if test_resource_id:
            kwargs["Prefix"] = f"{test_resource_id}/"
        response = s3_client.list_objects_v2(**kwargs)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_list_objects_contains_uploaded_key(
        self, s3_client, test_bucket, unique_prefix
    ):
        """An object that was just uploaded must appear in the listing."""
        key = f"{unique_prefix}/list-probe.txt"
        s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"probe")

        try:
            prefix_dir = key.rsplit("/", 1)[0] + "/"
            response = s3_client.list_objects_v2(
                Bucket=test_bucket, Prefix=prefix_dir
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            assert key in keys
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)


# ---------------------------------------------------------------------------
# Put object
# ---------------------------------------------------------------------------

class TestPutObject:
    def test_put_small_object(self, s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/small.txt"
        response = s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=b"Hello, HydroShare!",
            ContentType="text/plain",
        )
        try:
            assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_put_binary_object(self, s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/binary.bin"
        data = bytes(range(256)) * 64  # 16 KiB of binary data
        response = s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=data,
            ContentType="application/octet-stream",
        )
        try:
            assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)


# ---------------------------------------------------------------------------
# Get object
# ---------------------------------------------------------------------------

class TestGetObject:
    def test_get_returns_correct_body(self, s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/roundtrip.txt"
        payload = b"Round-trip payload " + os.urandom(32)
        s3_client.put_object(Bucket=test_bucket, Key=key, Body=payload)

        try:
            response = s3_client.get_object(Bucket=test_bucket, Key=key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            body = response["Body"].read()
            assert body == payload
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_get_returns_correct_content_type(
        self, s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/typed.json"
        s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=b'{"key": "value"}',
            ContentType="application/json",
        )
        try:
            response = s3_client.get_object(Bucket=test_bucket, Key=key)
            assert "application/json" in response["ContentType"]
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)


# ---------------------------------------------------------------------------
# Delete object
# ---------------------------------------------------------------------------

class TestDeleteObject:
    def test_delete_removes_object(self, s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/to-delete.txt"
        s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"delete me")

        delete_response = s3_client.delete_object(Bucket=test_bucket, Key=key)
        assert delete_response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)

        # Object must no longer appear in the listing.
        prefix_dir = key.rsplit("/", 1)[0] + "/"
        list_response = s3_client.list_objects_v2(
            Bucket=test_bucket, Prefix=prefix_dir
        )
        remaining_keys = [obj["Key"] for obj in list_response.get("Contents", [])]
        assert key not in remaining_keys

    def test_delete_nonexistent_object_is_idempotent(
        self, s3_client, test_bucket, unique_prefix
    ):
        """Deleting a key that does not exist must not raise an error."""
        key = f"{unique_prefix}/nonexistent-{os.urandom(8).hex()}.txt"
        response = s3_client.delete_object(Bucket=test_bucket, Key=key)
        assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)


# ---------------------------------------------------------------------------
# Multipart upload
# ---------------------------------------------------------------------------

class TestMultipartUpload:
    # S3 minimum part size is 5 MiB for all parts except the last.
    _PART_SIZE = 5 * 1024 * 1024  # 5 MiB

    def test_multipart_upload_two_parts(self, s3_client, test_bucket, unique_prefix):
        """Create an MPU, upload two parts, complete – verify the object body."""
        key = f"{unique_prefix}/multipart.bin"

        # Create multipart upload
        mpu = s3_client.create_multipart_upload(
            Bucket=test_bucket, Key=key, ContentType="application/octet-stream"
        )
        upload_id = mpu["UploadId"]

        part_data = [
            os.urandom(self._PART_SIZE),   # part 1 – exactly 5 MiB
            os.urandom(1024),              # part 2 – final part, any size
        ]
        parts = []

        try:
            for part_number, data in enumerate(part_data, start=1):
                response = s3_client.upload_part(
                    Bucket=test_bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=data,
                )
                assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
                parts.append({"PartNumber": part_number, "ETag": response["ETag"]})

            complete_response = s3_client.complete_multipart_upload(
                Bucket=test_bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            assert complete_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            # Verify round-trip integrity
            get_response = s3_client.get_object(Bucket=test_bucket, Key=key)
            body = get_response["Body"].read()
            assert body == part_data[0] + part_data[1]

        except Exception:
            # Attempt to abort so we don't leave dangling MPUs on failure.
            try:
                s3_client.abort_multipart_upload(
                    Bucket=test_bucket, Key=key, UploadId=upload_id
                )
            except Exception:
                pass
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=test_bucket, Key=key)
            except Exception:
                pass

    def test_abort_multipart_upload(self, s3_client, test_bucket, unique_prefix):
        """Abort an in-progress MPU – the key must not exist afterwards."""
        key = f"{unique_prefix}/aborted.bin"

        mpu = s3_client.create_multipart_upload(Bucket=test_bucket, Key=key)
        upload_id = mpu["UploadId"]

        # Upload one part so the MPU is genuinely in progress.
        s3_client.upload_part(
            Bucket=test_bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=1,
            Body=os.urandom(self._PART_SIZE),
        )

        abort_response = s3_client.abort_multipart_upload(
            Bucket=test_bucket, Key=key, UploadId=upload_id
        )
        assert abort_response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)

        # The key must not be present after abort.
        prefix_dir = key.rsplit("/", 1)[0] + "/"
        list_response = s3_client.list_objects_v2(
            Bucket=test_bucket, Prefix=prefix_dir
        )
        remaining_keys = [obj["Key"] for obj in list_response.get("Contents", [])]
        assert key not in remaining_keys

    def test_multipart_upload_streaming_via_file_object(
        self, s3_client, test_bucket, unique_prefix
    ):
        """Upload using a file-like object (common real-world pattern)."""
        key = f"{unique_prefix}/stream-multipart.bin"

        # Build ~11 MiB payload so we get two real parts.
        payload = os.urandom(self._PART_SIZE * 2 + 512)
        file_obj = io.BytesIO(payload)

        mpu = s3_client.create_multipart_upload(Bucket=test_bucket, Key=key)
        upload_id = mpu["UploadId"]
        parts = []

        try:
            part_number = 1
            while True:
                chunk = file_obj.read(self._PART_SIZE)
                if not chunk:
                    break
                response = s3_client.upload_part(
                    Bucket=test_bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                part_number += 1

            s3_client.complete_multipart_upload(
                Bucket=test_bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

            get_response = s3_client.get_object(Bucket=test_bucket, Key=key)
            body = get_response["Body"].read()
            assert body == payload

        except Exception:
            try:
                s3_client.abort_multipart_upload(
                    Bucket=test_bucket, Key=key, UploadId=upload_id
                )
            except Exception:
                pass
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=test_bucket, Key=key)
            except Exception:
                pass


# ===========================================================================
# Session-cookie auth variants
# The test logic is identical; only the client fixture differs.
# ===========================================================================

class TestSessionListObjects:
    def test_list_objects_returns_ok(
        self, session_s3_client, test_bucket, test_resource_id
    ):
        kwargs = {"Bucket": test_bucket}
        if test_resource_id:
            kwargs["Prefix"] = f"{test_resource_id}/"
        response = session_s3_client.list_objects_v2(**kwargs)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    def test_list_objects_contains_uploaded_key(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/list-probe-session.txt"
        session_s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"probe")

        try:
            prefix_dir = key.rsplit("/", 1)[0] + "/"
            response = session_s3_client.list_objects_v2(
                Bucket=test_bucket, Prefix=prefix_dir
            )
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            assert key in keys
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)


class TestSessionPutObject:
    def test_put_small_object(self, session_s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/small-session.txt"
        response = session_s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=b"Hello, HydroShare (session)!",
            ContentType="text/plain",
        )
        try:
            assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_put_binary_object(self, session_s3_client, test_bucket, unique_prefix):
        key = f"{unique_prefix}/binary-session.bin"
        data = bytes(range(256)) * 64
        response = session_s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=data,
            ContentType="application/octet-stream",
        )
        try:
            assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)


class TestSessionGetObject:
    def test_get_returns_correct_body(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/roundtrip-session.txt"
        payload = b"Round-trip session payload " + os.urandom(32)
        session_s3_client.put_object(Bucket=test_bucket, Key=key, Body=payload)

        try:
            response = session_s3_client.get_object(Bucket=test_bucket, Key=key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
            body = response["Body"].read()
            assert body == payload
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_get_returns_correct_content_type(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/typed-session.json"
        session_s3_client.put_object(
            Bucket=test_bucket,
            Key=key,
            Body=b'{"session": true}',
            ContentType="application/json",
        )
        try:
            response = session_s3_client.get_object(Bucket=test_bucket, Key=key)
            assert "application/json" in response["ContentType"]
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)


class TestSessionDeleteObject:
    def test_delete_removes_object(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/to-delete-session.txt"
        session_s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"delete me")

        delete_response = session_s3_client.delete_object(Bucket=test_bucket, Key=key)
        assert delete_response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)

        prefix_dir = key.rsplit("/", 1)[0] + "/"
        list_response = session_s3_client.list_objects_v2(
            Bucket=test_bucket, Prefix=prefix_dir
        )
        remaining_keys = [obj["Key"] for obj in list_response.get("Contents", [])]
        assert key not in remaining_keys

    def test_delete_nonexistent_object_is_idempotent(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/nonexistent-session-{os.urandom(8).hex()}.txt"
        response = session_s3_client.delete_object(Bucket=test_bucket, Key=key)
        assert response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)


class TestSessionMultipartUpload:
    _PART_SIZE = 5 * 1024 * 1024  # 5 MiB

    def test_multipart_upload_two_parts(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/multipart-session.bin"

        mpu = session_s3_client.create_multipart_upload(
            Bucket=test_bucket, Key=key, ContentType="application/octet-stream"
        )
        upload_id = mpu["UploadId"]

        part_data = [
            os.urandom(self._PART_SIZE),
            os.urandom(1024),
        ]
        parts = []

        try:
            for part_number, data in enumerate(part_data, start=1):
                response = session_s3_client.upload_part(
                    Bucket=test_bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=data,
                )
                assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
                parts.append({"PartNumber": part_number, "ETag": response["ETag"]})

            complete_response = session_s3_client.complete_multipart_upload(
                Bucket=test_bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            assert complete_response["ResponseMetadata"]["HTTPStatusCode"] == 200

            get_response = session_s3_client.get_object(Bucket=test_bucket, Key=key)
            body = get_response["Body"].read()
            assert body == part_data[0] + part_data[1]

        except Exception:
            try:
                session_s3_client.abort_multipart_upload(
                    Bucket=test_bucket, Key=key, UploadId=upload_id
                )
            except Exception:
                pass
            raise
        finally:
            try:
                session_s3_client.delete_object(Bucket=test_bucket, Key=key)
            except Exception:
                pass

    def test_abort_multipart_upload(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/aborted-session.bin"

        mpu = session_s3_client.create_multipart_upload(Bucket=test_bucket, Key=key)
        upload_id = mpu["UploadId"]

        session_s3_client.upload_part(
            Bucket=test_bucket,
            Key=key,
            UploadId=upload_id,
            PartNumber=1,
            Body=os.urandom(self._PART_SIZE),
        )

        abort_response = session_s3_client.abort_multipart_upload(
            Bucket=test_bucket, Key=key, UploadId=upload_id
        )
        assert abort_response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)

        prefix_dir = key.rsplit("/", 1)[0] + "/"
        list_response = session_s3_client.list_objects_v2(
            Bucket=test_bucket, Prefix=prefix_dir
        )
        remaining_keys = [obj["Key"] for obj in list_response.get("Contents", [])]
        assert key not in remaining_keys

    def test_multipart_upload_streaming_via_file_object(
        self, session_s3_client, test_bucket, unique_prefix
    ):
        key = f"{unique_prefix}/stream-multipart-session.bin"

        payload = os.urandom(self._PART_SIZE * 2 + 512)
        file_obj = io.BytesIO(payload)

        mpu = session_s3_client.create_multipart_upload(Bucket=test_bucket, Key=key)
        upload_id = mpu["UploadId"]
        parts = []

        try:
            part_number = 1
            while True:
                chunk = file_obj.read(self._PART_SIZE)
                if not chunk:
                    break
                response = session_s3_client.upload_part(
                    Bucket=test_bucket,
                    Key=key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                part_number += 1

            session_s3_client.complete_multipart_upload(
                Bucket=test_bucket,
                Key=key,
                UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )

            get_response = session_s3_client.get_object(Bucket=test_bucket, Key=key)
            body = get_response["Body"].read()
            assert body == payload

        except Exception:
            try:
                session_s3_client.abort_multipart_upload(
                    Bucket=test_bucket, Key=key, UploadId=upload_id
                )
            except Exception:
                pass
            raise
        finally:
            try:
                session_s3_client.delete_object(Bucket=test_bucket, Key=key)
            except Exception:
                pass


# ===========================================================================
# Event-service checks
# Verify that writes enqueue Celery tasks through Redis.
# ===========================================================================

class TestEventService:
    """Verify S3 writes enqueue expected Celery tasks via Redis."""

    @staticmethod
    def _capture_redis_commands_during(trigger, timeout_seconds=2.5):
        redis_host = os.environ.get("REDIS_HOST", "localhost")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))
        redis_db = int(os.environ.get("REDIS_DB", "0"))
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True,
        )

        commands = []
        ready = threading.Event()

        def _watch():
            with client.monitor() as monitor:
                ready.set()
                deadline = time.time() + timeout_seconds
                for item in monitor.listen():
                    command = item.get("command", "")
                    if command:
                        commands.append(command)
                    if time.time() >= deadline:
                        break

        watcher = threading.Thread(target=_watch, daemon=True)
        watcher.start()
        assert ready.wait(1.0), "Redis MONITOR did not start in time"

        # Give MONITOR a moment to subscribe before triggering the S3 request.
        time.sleep(0.1)
        trigger()
        watcher.join(timeout_seconds + 1.0)
        return commands

    @staticmethod
    def _count_task_pushes(commands, task_name, object_path):
        return sum(
            1
            for cmd in commands
            if "LPUSH" in cmd and task_name in cmd and object_path in cmd
        )

    def test_put_object_calls_event_service(
        self, s3_client, test_bucket, unique_prefix,
    ):
        """A SigV4 PutObject must enqueue hs_event_s3 and extract tasks."""
        key = f"{unique_prefix}/event-check.txt"

        commands = self._capture_redis_commands_during(
            lambda: s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"event check")
        )
        try:
            assert self._count_task_pushes(commands, "hs_event_s3.tasks.process_s3_event", key) >= 1
            assert self._count_task_pushes(commands, "hs_extract.tasks.extract_metadata", key) >= 1
        finally:
            s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_complete_multipart_calls_event_service(
        self, s3_client, test_bucket, unique_prefix,
    ):
        """A CompleteMultipartUpload must enqueue hs_event_s3 and extract tasks."""
        _PART_SIZE = 5 * 1024 * 1024
        key = f"{unique_prefix}/event-check-mpu.bin"

        mpu = s3_client.create_multipart_upload(Bucket=test_bucket, Key=key)
        upload_id = mpu["UploadId"]
        part = s3_client.upload_part(
            Bucket=test_bucket, Key=key, UploadId=upload_id,
            PartNumber=1, Body=os.urandom(_PART_SIZE),
        )
        try:
            commands = self._capture_redis_commands_during(
                lambda: s3_client.complete_multipart_upload(
                    Bucket=test_bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": [{"PartNumber": 1, "ETag": part["ETag"]}]},
                )
            )
            assert self._count_task_pushes(commands, "hs_event_s3.tasks.process_s3_event", key) >= 1
            assert self._count_task_pushes(commands, "hs_extract.tasks.extract_metadata", key) >= 1
        except Exception:
            try:
                s3_client.abort_multipart_upload(
                    Bucket=test_bucket, Key=key, UploadId=upload_id
                )
            except Exception:
                pass
            raise
        finally:
            try:
                s3_client.delete_object(Bucket=test_bucket, Key=key)
            except Exception:
                pass

    def test_session_put_object_calls_event_service(
        self, session_s3_client, test_bucket, unique_prefix,
    ):
        """A session-auth PutObject must enqueue hs_event_s3 and extract tasks."""
        key = f"{unique_prefix}/event-check-session.txt"

        commands = self._capture_redis_commands_during(
            lambda: session_s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"event check")
        )
        try:
            assert self._count_task_pushes(commands, "hs_event_s3.tasks.process_s3_event", key) >= 1
            assert self._count_task_pushes(commands, "hs_extract.tasks.extract_metadata", key) >= 1
        finally:
            session_s3_client.delete_object(Bucket=test_bucket, Key=key)

    def test_deleteobjects_posts_event_for_each_object(
        self, s3_client, test_bucket, unique_prefix,
    ):
        """DeleteObjects must enqueue at least one hs_event_s3 task."""
        keys = [
            f"{unique_prefix}/event-delete-one.txt",
            f"{unique_prefix}/event-delete-two.txt",
        ]

        for key in keys:
            s3_client.put_object(Bucket=test_bucket, Key=key, Body=b"event delete")

        delete_response = {}
        commands = self._capture_redis_commands_during(
            lambda: delete_response.update(
                s3_client.delete_objects(
                    Bucket=test_bucket,
                    Delete={"Objects": [{"Key": key} for key in keys]},
                )
            )
        )
        assert delete_response["ResponseMetadata"]["HTTPStatusCode"] in (200, 204)

        deleted_keys = {obj["Key"] for obj in delete_response.get("Deleted", [])}
        for key in keys:
            assert key in deleted_keys

        deleteobjects_pushes = sum(
            1
            for cmd in commands
            if "LPUSH" in cmd
            and "hs_event_s3.tasks.process_s3_event" in cmd
            and "s3:DeleteObjects" in cmd
        )
        assert deleteobjects_pushes >= 1
