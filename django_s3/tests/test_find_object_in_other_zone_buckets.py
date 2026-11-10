from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.test import SimpleTestCase

from django_s3.settings import ZoneConfig, ZonesConfig
from django_s3.storage import S3Storage

OBJECT_KEY = "res1/.hsjsonld/dataset_metadata.json"


def _zone(bucket_name):
    return ZoneConfig(
        aws_access_key_id="key",
        aws_secret_access_key="secret",
        aws_s3_endpoint_url="http://s3",
        aws_s3_endpoint_url_public="http://s3",
        bucket_name=bucket_name,
    )


ZONES = ZonesConfig(
    resource_s3_zones_config={
        "hydroshare": _zone("resource"),
        "published": _zone("published"),
        "ciroh": _zone("ciroh"),
    },
    resource_s3_default_zone="hydroshare",
)


def _client_error(code):
    return ClientError({"Error": {"Code": code}}, "HeadObject")


class TestFindObjectInOtherZoneBuckets(SimpleTestCase):

    def setUp(self):
        self.clients = {zone: MagicMock(name=zone) for zone in ZONES.resource_s3_zones_config}
        patch("django_s3.s3_backend.get_resource_s3_zones_config", return_value=ZONES).start()
        patch.object(
            S3Storage, "connection", lambda _self, zone: MagicMock(meta=MagicMock(client=self.clients[zone]))
        ).start()
        self.addCleanup(patch.stopall)
        self.storage = S3Storage()

    def test_returns_other_bucket_holding_the_object(self):
        """The excluded bucket is skipped; the bucket where the object still exists is returned."""
        self.clients["published"].head_object.side_effect = _client_error("404")
        self.assertEqual(
            self.storage.find_object_in_other_zone_buckets(OBJECT_KEY, exclude_bucket="resource"),
            f"ciroh/{OBJECT_KEY}",
        )
        self.clients["hydroshare"].head_object.assert_not_called()
        self.clients["ciroh"].head_object.assert_called_once_with(Bucket="ciroh", Key=OBJECT_KEY)

    def test_returns_published_bucket_after_resource_bucket_move(self):
        """A published copy is found, checked with the published zone's client."""
        self.clients["ciroh"].head_object.side_effect = _client_error("404")
        self.assertEqual(
            self.storage.find_object_in_other_zone_buckets(OBJECT_KEY, exclude_bucket="resource"),
            f"published/{OBJECT_KEY}",
        )
        self.clients["hydroshare"].head_object.assert_not_called()
        self.clients["published"].head_object.assert_called_once_with(Bucket="published", Key=OBJECT_KEY)

    def test_returns_none_when_no_other_bucket_has_object(self):
        self.clients["published"].head_object.side_effect = _client_error("404")
        self.clients["ciroh"].head_object.side_effect = _client_error("NoSuchKey")
        self.assertIsNone(self.storage.find_object_in_other_zone_buckets(OBJECT_KEY, exclude_bucket="resource"))

    def test_reraises_non_not_found_errors(self):
        """Access/server errors propagate so callers don't mistake them for the object being absent."""
        self.clients["published"].head_object.side_effect = _client_error("403")
        with self.assertRaises(ClientError):
            self.storage.find_object_in_other_zone_buckets(OBJECT_KEY, exclude_bucket="resource")
