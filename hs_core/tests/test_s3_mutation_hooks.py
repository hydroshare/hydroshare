import uuid
from unittest.mock import patch

from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib.auth.models import Group
from django.test import TestCase

from hs_access_control.models import PrivilegeCodes
from hs_core import hydroshare
from hs_core.testing import MockS3TestCaseMixin

EVENT_TASK = "hs_event_s3.tasks.process_s3_event"
DISCOVERY_TASK = "hs_event_s3.tasks.sync_discovery_collection"
EXTRACT_TASK = "hs_extract.tasks.extract_metadata"

SRC_ZONE = "hydroshare"
DST_ZONE = "ciroh"
SRC_BUCKET = settings.RESOURCE_S3_ZONES_CONFIG[SRC_ZONE]["bucket_name"]
DST_BUCKET = settings.RESOURCE_S3_ZONES_CONFIG[DST_ZONE]["bucket_name"]
METADATA_BODY = b'{"name": "copy object test"}'


class TestS3CopyObjectMutationHook(MockS3TestCaseMixin, TestCase):
    """Server-side copies (e.g. a quota holder change across zones) must emit S3 events like uploads do."""

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
        self.client = self.res.get_s3_storage().connection(SRC_ZONE).meta.client
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
