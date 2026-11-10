import hashlib
import io
import socket
import uuid
from unittest.mock import patch
from urllib.parse import urlsplit

from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin, override_zone_config

EVENT_TASK = "hs_event_s3.tasks.process_s3_event"
DISCOVERY_TASK = "hs_event_s3.tasks.sync_discovery_collection"
EXTRACT_TASK = "hs_extract.tasks.extract_metadata"

SRC_ZONE = "hydroshare"
DST_ZONE = "ciroh"
SRC_BUCKET = settings.RESOURCE_S3_ZONES_CONFIG[SRC_ZONE]["bucket_name"]
DST_BUCKET = settings.RESOURCE_S3_ZONES_CONFIG[DST_ZONE]["bucket_name"]
METADATA_BODY = b'{"name": "copy object test"}'
MiB = 1024 * 1024
# S3 minimum part size; with an ~11 MiB object, boto3 client.copy() issues several UploadPartCopy calls
MULTIPART_THRESHOLD = 5 * MiB
LARGE_BODY = bytes(range(256)) * (11 * MiB // 256)


class S3CopyHookTestBase(MockS3TestCaseMixin, TestCase):
    """Resource in the source zone with a dataset_metadata.json, an owner in the destination zone, and celery
    send_task patched to capture the S3 mutation events."""

    def setUp(self):
        super().setUp()
        self.celery_app = patch("django_s3.s3_backend.celery_app").start()
        self.addCleanup(patch.stopall)

        group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.owner = hydroshare.create_account(
            'copy_owner@email.com',
            username='copy_owner' + uuid.uuid4().hex,
            first_name='owner_first_name',
            last_name='owner_last_name',
            superuser=False,
            groups=[group]
        )
        self.ciroh_owner = hydroshare.create_account(
            'copy_ciroh_owner@email.com',
            username='copy_ciroh_owner' + uuid.uuid4().hex,
            first_name='ciroh_first_name',
            last_name='ciroh_last_name',
            superuser=False,
            groups=[group]
        )
        quota = self.ciroh_owner.quotas.first()
        quota.zone = DST_ZONE
        quota.save()

        self.res = hydroshare.create_resource('CompositeResource', self.owner, 'Copy Object Hook Test')
        self.owner.uaccess.share_resource_with_user(self.res, self.ciroh_owner, PrivilegeCodes.OWNER)

        # source-zone client, as used by S3Storage.new_quota_holder for the cross-bucket copy
        self.storage = self.res.get_s3_storage()
        self.client = self.storage.connection(SRC_ZONE).meta.client
        self.metadata_key = f"{self.res.short_id}/.hsjsonld/dataset_metadata.json"
        self.client.put_object(Bucket=SRC_BUCKET, Key=self.metadata_key, Body=METADATA_BODY)
        self.celery_app.reset_mock()

    def tearDown(self):
        for bucket in (SRC_BUCKET, DST_BUCKET):
            self._delete_objects(bucket, f"{self.res.short_id}/")
        super().tearDown()

    def _delete_objects(self, bucket, prefix):
        listing = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in listing.get("Contents", []):
            self.client.delete_object(Bucket=bucket, Key=obj["Key"])

    def _sent(self, task_name):
        return [c.kwargs["kwargs"] for c in self.celery_app.send_task.call_args_list if c.args[0] == task_name]

    def _copy_to_dst(self, key):
        self.client.copy_object(Bucket=DST_BUCKET, Key=key, CopySource={"Bucket": SRC_BUCKET, "Key": key})


class TestS3CopyObjectMutationHook(S3CopyHookTestBase):
    """Server-side copies (e.g. a quota holder change across zones) must emit S3 events like uploads do."""

    def test_copy_of_dataset_metadata_dispatches_discovery_sync_for_destination(self):
        self._copy_to_dst(self.metadata_key)

        discovery_events = self._sent(DISCOVERY_TASK)
        self.assertEqual(len(discovery_events), 1)
        event = discovery_events[0]
        self.assertEqual(event["action"], "s3:CopyObject")
        self.assertEqual(event["bucket"], DST_BUCKET)
        self.assertEqual(event["object_path"], self.metadata_key)
        # zone of the destination bucket, even though the copy was issued with the source-zone client
        self.assertEqual(event["zone"], DST_ZONE)
        self.assertEqual(event["file_size"], len(METADATA_BODY))
        self.assertEqual(event["copy_source"], f"{SRC_BUCKET}/{self.metadata_key}")
        self.assertEqual(len(self._sent(EVENT_TASK)), 1)
        self.assertEqual(self._sent(EXTRACT_TASK), [])

    def test_copy_of_data_file_dispatches_extraction(self):
        data_key = f"{self.res.short_id}/data/contents/copy_test.txt"
        self.client.put_object(Bucket=SRC_BUCKET, Key=data_key, Body=b"some data")
        self.celery_app.reset_mock()

        self._copy_to_dst(data_key)

        extract_events = self._sent(EXTRACT_TASK)
        self.assertEqual(len(extract_events), 1)
        self.assertEqual(extract_events[0]["action"], "s3:CopyObject")
        self.assertEqual(extract_events[0]["bucket"], DST_BUCKET)
        self.assertEqual(extract_events[0]["object_path"], data_key)
        self.assertEqual(extract_events[0]["zone"], DST_ZONE)
        self.assertEqual(extract_events[0]["copy_source"], f"{SRC_BUCKET}/{data_key}")
        self.assertEqual(len(self._sent(EVENT_TASK)), 1)
        self.assertEqual(self._sent(DISCOVERY_TASK), [])

    def test_copy_with_string_copy_source_reports_source(self):
        data_key = f"{self.res.short_id}/data/contents/copy_test.txt"
        self.client.put_object(Bucket=SRC_BUCKET, Key=data_key, Body=b"some data")
        self.celery_app.reset_mock()

        self.client.copy_object(Bucket=DST_BUCKET, Key=data_key, CopySource=f"{SRC_BUCKET}/{data_key}")

        extract_events = self._sent(EXTRACT_TASK)
        self.assertEqual(len(extract_events), 1)
        self.assertEqual(extract_events[0]["copy_source"], f"{SRC_BUCKET}/{data_key}")

    def test_rename_reports_source_of_copy(self):
        src_key = f"{self.res.short_id}/data/contents/old_name.txt"
        dst_key = f"{self.res.short_id}/data/contents/new_name.txt"
        self.client.put_object(Bucket=SRC_BUCKET, Key=src_key, Body=b"some data")
        self.celery_app.reset_mock()

        self.res.get_s3_storage().moveFile(src_key, dst_key)

        copy_events = [e for e in self._sent(EXTRACT_TASK) if e["action"] == "s3:CopyObject"]
        self.assertEqual(len(copy_events), 1)
        self.assertEqual(copy_events[0]["bucket"], SRC_BUCKET)
        self.assertEqual(copy_events[0]["object_path"], dst_key)
        self.assertEqual(copy_events[0]["copy_source"], f"{SRC_BUCKET}/{src_key}")

    def test_resource_copy_reports_source_with_same_path_in_new_resource(self):
        """copyFiles of a folder (as in a resource copy) keeps each file's path within the resource."""
        new_res = hydroshare.create_resource('CompositeResource', self.owner, 'Copy Files Hook Test')
        self.addCleanup(self._delete_objects, SRC_BUCKET, f"{new_res.short_id}/")
        rel_paths = ["data/contents/file1.txt", "data/contents/folder/file2.txt"]
        for rel_path in rel_paths:
            self.client.put_object(Bucket=SRC_BUCKET, Key=f"{self.res.short_id}/{rel_path}", Body=b"some data")
        self.celery_app.reset_mock()

        self.res.get_s3_storage().copyFiles(f"{self.res.short_id}/data/contents",
                                            f"{new_res.short_id}/data/contents")

        copy_events = {e["object_path"]: e for e in self._sent(EXTRACT_TASK) if e["action"] == "s3:CopyObject"}
        self.assertEqual(set(copy_events), {f"{new_res.short_id}/{rel_path}" for rel_path in rel_paths})
        for rel_path in rel_paths:
            event = copy_events[f"{new_res.short_id}/{rel_path}"]
            self.assertEqual(event["bucket"], SRC_BUCKET)
            self.assertEqual(event["copy_source"], f"{SRC_BUCKET}/{self.res.short_id}/{rel_path}")
        # a copy leaves the source in place
        self.assertEqual([e for e in self._sent(EVENT_TASK) if e["action"] == "s3:DeleteObjects"], [])

    def test_failed_copy_dispatches_nothing(self):
        missing_key = f"{self.res.short_id}/data/contents/does_not_exist.txt"
        with self.assertRaises(ClientError):
            self._copy_to_dst(missing_key)
        self.celery_app.send_task.assert_not_called()

    def test_quota_holder_change_across_zones_dispatches_discovery_sync_for_destination(self):
        self.res.set_quota_holder(self.owner, self.ciroh_owner)

        copy_events = [e for e in self._sent(DISCOVERY_TASK) if e["action"] == "s3:CopyObject"]
        self.assertEqual(len(copy_events), 1)
        self.assertEqual(copy_events[0]["bucket"], DST_BUCKET)
        self.assertEqual(copy_events[0]["object_path"], self.metadata_key)
        self.assertEqual(copy_events[0]["zone"], DST_ZONE)
        self.assertEqual(copy_events[0]["copy_source"], f"{SRC_BUCKET}/{self.metadata_key}")


class TestS3MultipartCopyMutationHook(S3CopyHookTestBase):
    """A copy into a "managed_copy" zone (AWS) may run as a multipart UploadPartCopy instead of a CopyObject; its
    completion must be reported exactly like the single CopyObject it replaces. A "copy_object" zone (GCS, which
    does not implement UploadPartCopy) must never issue UploadPartCopy."""

    def setUp(self):
        super().setUp()
        self.data_key = f"{self.res.short_id}/data/contents/large_file.bin"
        self.operation_counts = {}
        events = self.client.meta.events
        for operation in ("CopyObject", "UploadPartCopy", "CompleteMultipartUpload"):
            handler = self._make_counter(operation)
            events.register(f"before-call.s3.{operation}", handler)
            self.addCleanup(events.unregister, f"before-call.s3.{operation}", handler)

    def _make_counter(self, operation):
        def count(**kwargs):
            self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1
        return count

    def _put_large_file(self):
        self.client.put_object(Bucket=SRC_BUCKET, Key=self.data_key, Body=LARGE_BODY)
        self.celery_app.reset_mock()

    def _copy(self, key):
        self.storage._copy_object(key, key, SRC_BUCKET, SRC_ZONE, DST_BUCKET, DST_ZONE)

    def _dst_md5(self, key):
        body = self.client.get_object(Bucket=DST_BUCKET, Key=key)["Body"].read()
        return hashlib.md5(body).hexdigest()

    def test_managed_multipart_copy_reports_copy_object(self):
        override_zone_config(self, DST_ZONE, copy_method="managed_copy", multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()

        self._copy(self.data_key)

        self.assertGreater(self.operation_counts.get("UploadPartCopy", 0), 1)
        self.assertEqual(self.operation_counts.get("CopyObject", 0), 0)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())
        events = self._sent(EVENT_TASK)
        self.assertEqual(len(events), 1)
        extract_events = self._sent(EXTRACT_TASK)
        self.assertEqual(len(extract_events), 1)
        event = extract_events[0]
        self.assertEqual(event["action"], "s3:CopyObject")
        self.assertEqual(event["bucket"], DST_BUCKET)
        self.assertEqual(event["object_path"], self.data_key)
        self.assertEqual(event["zone"], DST_ZONE)
        self.assertEqual(event["file_size"], len(LARGE_BODY))
        self.assertEqual(event["copy_source"], f"{SRC_BUCKET}/{self.data_key}")

    def test_managed_copy_below_threshold_uses_copy_object(self):
        override_zone_config(self, DST_ZONE, copy_method="managed_copy", multipart_copy_threshold=MULTIPART_THRESHOLD)

        self._copy(self.metadata_key)

        self.assertEqual(self.operation_counts.get("UploadPartCopy", 0), 0)
        self.assertEqual(self.operation_counts.get("CopyObject", 0), 1)
        discovery_events = self._sent(DISCOVERY_TASK)
        self.assertEqual(len(discovery_events), 1)
        self.assertEqual(discovery_events[0]["action"], "s3:CopyObject")
        self.assertEqual(discovery_events[0]["zone"], DST_ZONE)
        self.assertEqual(discovery_events[0]["copy_source"], f"{SRC_BUCKET}/{self.metadata_key}")

    def test_copy_object_zone_never_issues_upload_part_copy(self):
        # default copy_method, as configured for GCS zones
        self._put_large_file()

        self._copy(self.data_key)

        self.assertEqual(self.operation_counts.get("UploadPartCopy", 0), 0)
        self.assertEqual(self.operation_counts.get("CopyObject", 0), 1)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())
        extract_events = self._sent(EXTRACT_TASK)
        self.assertEqual(len(extract_events), 1)
        self.assertEqual(extract_events[0]["action"], "s3:CopyObject")

    def test_multipart_upload_is_not_reported_as_copy(self):
        self.client.upload_fileobj(io.BytesIO(LARGE_BODY), SRC_BUCKET, self.data_key,
                                   Config=TransferConfig(multipart_threshold=MULTIPART_THRESHOLD))

        self.assertGreater(self.operation_counts.get("CompleteMultipartUpload", 0), 0)
        events = self._sent(EVENT_TASK)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["action"], "s3:CompleteMultipartUpload")
        self.assertEqual(events[0]["zone"], SRC_ZONE)
        self.assertEqual(events[0]["file_size"], len(LARGE_BODY))
        self.assertNotIn("copy_source", events[0])

    def test_aborted_multipart_copy_dispatches_nothing(self):
        self._put_large_file()
        upload_id = self.client.create_multipart_upload(Bucket=DST_BUCKET, Key=self.data_key)["UploadId"]
        self.client.upload_part_copy(Bucket=DST_BUCKET, Key=self.data_key, UploadId=upload_id, PartNumber=1,
                                     CopySource={"Bucket": SRC_BUCKET, "Key": self.data_key})
        self.client.abort_multipart_upload(Bucket=DST_BUCKET, Key=self.data_key, UploadId=upload_id)

        self.celery_app.send_task.assert_not_called()

    def test_quota_holder_change_with_managed_multipart_copy(self):
        override_zone_config(self, DST_ZONE, copy_method="managed_copy", multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()

        self.res.set_quota_holder(self.owner, self.ciroh_owner)

        self.assertEqual(self.client.list_objects_v2(Bucket=SRC_BUCKET, Prefix=f"{self.res.short_id}/")
                         .get("KeyCount"), 0)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())
        copy_events = {e["object_path"]: e for e in self._sent(EVENT_TASK) if e["action"] == "s3:CopyObject"}
        for key in (self.metadata_key, self.data_key):
            self.assertEqual(copy_events[key]["bucket"], DST_BUCKET)
            self.assertEqual(copy_events[key]["zone"], DST_ZONE)
            self.assertEqual(copy_events[key]["copy_source"], f"{SRC_BUCKET}/{key}")
        self.assertEqual([e["object_path"] for e in self._sent(DISCOVERY_TASK) if e["action"] == "s3:CopyObject"],
                         [self.metadata_key])
        extract_copies = [e["object_path"] for e in self._sent(EXTRACT_TASK) if e["action"] == "s3:CopyObject"]
        self.assertIn(self.data_key, extract_copies)
        self.assertEqual([e for e in self._sent(EVENT_TASK) if e["action"] == "s3:CompleteMultipartUpload"], [])

    def test_zones_on_different_endpoints_stream_the_copy(self):
        # same MinIO server, but reached by IP instead of hostname, so the zones look like separate providers
        endpoint = urlsplit(settings.RESOURCE_S3_ZONES_CONFIG[DST_ZONE]["aws_s3_endpoint_url"])
        endpoint = endpoint._replace(netloc="%s:%s" % (socket.gethostbyname(endpoint.hostname), endpoint.port)).geturl()
        override_zone_config(self, DST_ZONE, aws_s3_endpoint_url=endpoint, copy_method="managed_copy",
                             multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()

        self._copy(self.data_key)

        self.assertEqual(self.operation_counts.get("CopyObject", 0), 0)
        self.assertEqual(self.operation_counts.get("UploadPartCopy", 0), 0)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())
        events = self._sent(EVENT_TASK)
        self.assertEqual(len(events), 1)
        # written by the destination-zone client as a plain upload, not a copy
        self.assertIn(events[0]["action"], ("s3:PutObject", "s3:CompleteMultipartUpload"))
        self.assertEqual(events[0]["bucket"], DST_BUCKET)
        self.assertEqual(events[0]["zone"], DST_ZONE)
        self.assertNotIn("copy_source", events[0])

    def test_copy_object_size_cap_falls_back_to_managed_copy(self):
        # a "copy_object" zone (the default) whose backend rejects CopyObject as too large (the AWS 5GB cap)
        # must fall back to a managed multipart copy instead of failing
        override_zone_config(self, DST_ZONE, multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()
        size_cap_error = ClientError(
            {"Error": {"Code": "InvalidRequest",
                       "Message": "The specified copy source is larger than the maximum allowable size "
                                  "for a copy source: 5368709120"}},
            "CopyObject",
        )

        with patch.object(self.client, "copy_object", side_effect=size_cap_error) as mock_copy_object:
            self._copy(self.data_key)

        mock_copy_object.assert_called_once()
        self.assertGreater(self.operation_counts.get("UploadPartCopy", 0), 1)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())
        extract_events = self._sent(EXTRACT_TASK)
        self.assertEqual(len(extract_events), 1)
        self.assertEqual(extract_events[0]["action"], "s3:CopyObject")
        self.assertEqual(extract_events[0]["copy_source"], f"{SRC_BUCKET}/{self.data_key}")

    def test_copy_object_other_errors_do_not_fall_back(self):
        # errors other than the size cap (permissions, quota, ...) must keep failing fast
        override_zone_config(self, DST_ZONE, multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()
        error = ClientError({"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}, "CopyObject")

        with patch.object(self.client, "copy_object", side_effect=error):
            with self.assertRaises(ClientError):
                self._copy(self.data_key)

        self.assertEqual(self.operation_counts.get("UploadPartCopy", 0), 0)

    def test_size_cap_fallback_caps_multipart_threshold(self):
        # a threshold configured above the CopyObject cap must not turn the fallback into another CopyObject
        override_zone_config(self, DST_ZONE, multipart_copy_threshold=100 * 1024 * MiB)
        self._put_large_file()
        size_cap_error = ClientError(
            {"Error": {"Code": "InvalidRequest",
                       "Message": "The specified copy source is larger than the maximum allowable size "
                                  "for a copy source: 5368709120"}},
            "CopyObject",
        )

        # stand in a small cap for AWS's 5GiB so an ~11 MiB object is "too large"
        with patch("django_s3.storage.COPY_OBJECT_MAX_SIZE", MULTIPART_THRESHOLD), \
                patch.object(self.client, "copy_object", side_effect=size_cap_error) as mock_copy_object:
            self._copy(self.data_key)

        mock_copy_object.assert_called_once()
        self.assertGreater(self.operation_counts.get("UploadPartCopy", 0), 1)
        self.assertEqual(self._dst_md5(self.data_key), hashlib.md5(LARGE_BODY).hexdigest())

    def test_size_cap_message_with_other_error_code_does_not_fall_back(self):
        override_zone_config(self, DST_ZONE, multipart_copy_threshold=MULTIPART_THRESHOLD)
        self._put_large_file()
        error = ClientError(
            {"Error": {"Code": "AccessDenied",
                       "Message": "maximum allowable size for a copy source"}},
            "CopyObject",
        )

        with patch.object(self.client, "copy_object", side_effect=error):
            with self.assertRaises(ClientError):
                self._copy(self.data_key)

        self.assertEqual(self.operation_counts.get("UploadPartCopy", 0), 0)
