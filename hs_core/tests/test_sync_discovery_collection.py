from unittest import TestCase
from unittest.mock import MagicMock, patch

from hydroshare.hydrocelery import app as hydroshare_celery_app
from hs_event_s3.tasks import sync_discovery_collection

# Importing hs_event_s3.tasks creates a second Celery app that becomes the current app for the whole test run,
# which detaches Django's shared tasks from the eager-mode config set by the test runner. Restore the hydroshare app.
hydroshare_celery_app.set_current()

TASKS = "hs_event_s3.tasks"
OBJECT_PATH = "res1/.hsjsonld/dataset_metadata.json"


class TestSyncDiscoveryCollectionDelete(TestCase):
    """Delete events for dataset_metadata.json, e.g. from the old bucket during a cross-zone move."""

    def setUp(self):
        self.collect = patch(f"{TASKS}.collect_file_to_catalog").start()
        self.delete = patch(f"{TASKS}.delete_file_from_catalog").start()
        self.find_live = patch(f"{TASKS}.find_live_metadata_file").start()
        self.resource_objects = patch(f"{TASKS}.BaseResource.objects").start()
        self.addCleanup(patch.stopall)

    def _set_resource(self, discoverable):
        if discoverable is None:
            self.resource_objects.filter.return_value.first.return_value = None
        else:
            res = MagicMock()
            res.raccess.discoverable = discoverable
            self.resource_objects.filter.return_value.first.return_value = res

    def _run_delete(self):
        sync_discovery_collection.run(action="s3:DeleteObjects", bucket="resource", object_path=OBJECT_PATH)

    def test_live_copy_in_other_bucket_and_discoverable_recollects(self):
        self.find_live.return_value = f"ciroh/{OBJECT_PATH}"
        self._set_resource(discoverable=True)
        self._run_delete()
        self.find_live.assert_called_once_with(OBJECT_PATH, exclude_bucket="resource")
        self.collect.assert_called_once_with(f"ciroh/{OBJECT_PATH}")
        self.delete.assert_not_called()

    def test_published_copy_after_resource_bucket_delete_recollects(self):
        self.find_live.return_value = f"published/{OBJECT_PATH}"
        self._set_resource(discoverable=True)
        self._run_delete()
        self.find_live.assert_called_once_with(OBJECT_PATH, exclude_bucket="resource")
        self.collect.assert_called_once_with(f"published/{OBJECT_PATH}")
        self.delete.assert_not_called()

    def test_no_live_copy_deletes(self):
        self.find_live.return_value = None
        self._run_delete()
        self.delete.assert_called_once_with(f"resource/{OBJECT_PATH}")
        self.collect.assert_not_called()

    def test_live_copy_not_discoverable_deletes(self):
        self.find_live.return_value = f"ciroh/{OBJECT_PATH}"
        self._set_resource(discoverable=False)
        self._run_delete()
        self.delete.assert_called_once_with(f"resource/{OBJECT_PATH}")
        self.collect.assert_not_called()

    def test_live_copy_resource_missing_deletes(self):
        self.find_live.return_value = f"ciroh/{OBJECT_PATH}"
        self._set_resource(discoverable=None)
        self._run_delete()
        self.delete.assert_called_once_with(f"resource/{OBJECT_PATH}")
        self.collect.assert_not_called()

    def test_lookup_error_retries_without_deleting(self):
        error = RuntimeError("head_object failed")
        self.find_live.side_effect = error
        with patch.object(sync_discovery_collection, "retry", side_effect=RuntimeError("retry")) as retry:
            with self.assertRaisesRegex(RuntimeError, "retry"):
                self._run_delete()
        retry.assert_called_once_with(exc=error)
        self.delete.assert_not_called()
        self.collect.assert_not_called()


class TestSyncDiscoveryCollectionCopy(TestCase):
    """Copy events for dataset_metadata.json, e.g. into the new bucket during a cross-zone move."""

    def setUp(self):
        self.collect = patch(f"{TASKS}.collect_file_to_catalog").start()
        self.delete = patch(f"{TASKS}.delete_file_from_catalog").start()
        self.resource_objects = patch(f"{TASKS}.BaseResource.objects").start()
        self.addCleanup(patch.stopall)

    def _run_copy(self, discoverable):
        self.resource_objects.get.return_value.raccess.discoverable = discoverable
        sync_discovery_collection.run(action="s3:CopyObject", bucket="ciroh", object_path=OBJECT_PATH)

    def test_copy_discoverable_collects_destination(self):
        self._run_copy(discoverable=True)
        self.resource_objects.get.assert_called_once_with(short_id="res1")
        self.collect.assert_called_once_with(f"ciroh/{OBJECT_PATH}")
        self.delete.assert_not_called()

    def test_copy_not_discoverable_deletes(self):
        self._run_copy(discoverable=False)
        self.resource_objects.get.assert_called_once_with(short_id="res1")
        self.delete.assert_called_once_with(f"ciroh/{OBJECT_PATH}")
        self.collect.assert_not_called()
